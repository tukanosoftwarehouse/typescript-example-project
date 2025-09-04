#!/usr/bin/env python3


import json
import os
import pathlib
import sys
from typing import List

import requests
from dotenv import load_dotenv
from llm_providers import LLMProviderFactory

load_dotenv()

class GitHubClient:
    """Consolidated GitHub API client for PR operations."""
    
    def __init__(self, token: str, api_url: str = "https://api.github.com"):
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"
        })
    
    def get_pr_files(self, repo: str, pr_number: int) -> List[dict]:
        """Fetch list of changed files for a PR."""
        url = f"{self.api_url}/repos/{repo}/pulls/{pr_number}/files"
        resp = self.session.get(url)
        
        if resp.status_code == 404:
            raise RuntimeError(f"PR {pr_number} not found in repo {repo} (404)")
        resp.raise_for_status()
        
        return resp.json()
    
    def get_pr_head_sha(self, repo: str, pr_number: int) -> str:
        """Get head commit SHA for a PR."""
        url = f"{self.api_url}/repos/{repo}/pulls/{pr_number}"
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        return data["head"]["sha"]
    
    def get_pr_diff(self, repo: str, pr_number: int) -> str:
        """Get unified diff for a PR directly from GitHub."""
        url = f"{self.api_url}/repos/{repo}/pulls/{pr_number}"
        headers = self.session.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.diff"
        
        resp = self.session.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text
    
    def submit_review(self, repo: str, pr_number: int, commit_sha: str, comments: List[dict]):
        """Submit a PR review with comments."""
        if not comments:
            print("ℹ️ Brak komentarzy do wysłania w review.")
            return
        
        payload = {
            "commit_id": commit_sha,
            "event": "COMMENT",
            "body": "Automated LLM review",
            "comments": comments
        }
        
        url = f"{self.api_url}/repos/{repo}/pulls/{pr_number}/reviews"
        resp = self.session.post(url, json=payload)
        
        if resp.status_code not in (200, 201):
            try:
                err = resp.json()
            except Exception:
                err = resp.text
            raise RuntimeError(f"GitHub review error {resp.status_code}: {err}")
        
        print("✅ Wysłano review z pakietem komentarzy.")


def add_line_numbers_to_diff(diff_text: str) -> str:
    """Add sequential line numbers (001:, 002:, etc.) to each line of the diff."""
    lines = diff_text.split('\n')
    numbered_lines = []
    
    for i, line in enumerate(lines, 1):
        numbered_lines.append(f"{i:03d}: {line}")
    
    return '\n'.join(numbered_lines)


def extract_file_line_number(numbered_line: str, diff_text: str, file_path: str) -> tuple[int, bool]:
    """Extract the actual file line number from diff for a given numbered line."""
    try:
        line_num = int(numbered_line)
        lines = diff_text.split('\n')
        
        if line_num > len(lines):
            return 0, False
            
        target_line = lines[line_num - 1]
        
        # Check if it's a change line
        is_change_line = target_line.startswith('+') or target_line.startswith('-')
        if not is_change_line:
            return 0, False
        
        # Find the file section and track line numbers
        current_file = None
        new_line_num = 0
        
        for i in range(line_num):
            line = lines[i]
            
            # Track which file we're in
            if line.startswith('+++ b/'):
                current_file = line[6:]  # Remove '+++ b/'
            
            # Parse hunk header to get starting line number
            elif line.startswith('@@'):
                # Format: @@ -old_start,old_count +new_start,new_count @@
                parts = line.split(' ')
                if len(parts) >= 3:
                    new_part = parts[2]  # +new_start,new_count
                    if new_part.startswith('+'):
                        new_line_num = int(new_part[1:].split(',')[0]) - 1  # Start from line before
            
            # Count lines in the new file (+ and context lines)
            elif current_file == file_path and (line.startswith('+') or line.startswith(' ')):
                new_line_num += 1
                
                # If this is our target line, return the line number
                if i == line_num - 1:
                    return new_line_num, True
        
        return 0, False
    except (ValueError, IndexError):
        return 0, False


def llm_review_chunk(llm_provider, chunk: str) -> List[dict]:
    """Call the LLM provider on a diff chunk and return list of comments."""
    # Pre-number the diff lines for stable references
    numbered_chunk = add_line_numbers_to_diff(chunk)
    
    system_prompt = (
        "You are performing a code review as a senior software engineer. In addition to low-level suggestions (null checks, logs), look for deeper architectural concerns: proper exception handling, code separation, testability, and whether the method fulfills its purpose cleanly. Be concise but precise. Look as well for naming code smells\n"
        "IMPORTANT: Use ONLY the provided numeric prefixes (001:, 002:, etc.) as line references.\n"
        "OUTPUT FORMAT: jednoznacznie poprawny JSON w formacie:\n"
        "[{'file_path': str, 'numbered_line': str, 'level': 'critical|suggestion|nitpick', 'comment': str}, ...]\n"
        "Example: {'file_path': 'src/main.ts', 'numbered_line': '042', 'level': 'suggestion', 'comment': 'Consider adding error handling'}"
    )
    
    try:
        return llm_provider.review_code(numbered_chunk, system_prompt)
    except Exception as e:
        raise RuntimeError(f'Error during LLM request: {e}')


def main() -> None:
    # Configuration
    out_file = os.getenv('OUT_FILE', 'review.json')
    repo = os.getenv('GITHUB_REPOSITORY', 'tukanosoftwarehouse/typescript-example-project')
    pr_number_str = os.getenv('PR_NUMBER', default="1")
    pr_number = int(pr_number_str) if pr_number_str is not None else None
    gh_token = os.getenv("GITHUB_TOKEN")
    llm_config_path = os.getenv('LLM_CONFIG_PATH', 'scripts/llm_config.yml')
    llm_provider_override = os.getenv('LLM_PROVIDER')

    # Validation
    if not gh_token:
        raise RuntimeError('Brak GITHUB_TOKEN w środowisku – wymagany do pracy z GitHubem')
    if not repo or not pr_number:
        raise RuntimeError('Brak owner/repo i numer PR przez zmienne środowiskowe GITHUB_REPOSITORY i PR_NUMBER')

    # Initialize clients
    try:
        llm_provider = LLMProviderFactory.create_from_config(
            config_path=llm_config_path,
            provider_override=llm_provider_override
        )
        print(f"🤖 Using provider: {llm_provider.get_model_info()}", file=sys.stderr)
    except Exception as e:
        raise RuntimeError(f'Błąd podczas inicjalizacji LLM providera: {e}')
    
    github_client = GitHubClient(gh_token)

    # Get diff from GitHub
    try:
        diff_text = github_client.get_pr_diff(repo, pr_number)
        if not diff_text.strip():
            print('ℹ️ No diff to review', file=sys.stderr)
            pathlib.Path(out_file).write_text('[]')
            return
    except Exception as exc:
        print(f'❌ Error getting diff: {exc}', file=sys.stderr)
        return

    # Get LLM review
    all_comments = []
    try:
        print(f'🔎 Reviewing full diff (size≈{len(diff_text)} chars)...', file=sys.stderr)
        all_comments = llm_review_chunk(llm_provider, diff_text)
        if not isinstance(all_comments, list):
            raise ValueError('LLM provider returned non-list response')
    except Exception as exc:
        print(f'⚠️  Error reviewing diff: {exc}', file=sys.stderr)

    # Save comments to file
    pathlib.Path(out_file).write_text(json.dumps(all_comments, indent=2, ensure_ascii=False))
    print(f'✅ Saved {len(all_comments)} comments to {out_file}')

    # Submit review to GitHub
    try:
        commit_sha = github_client.get_pr_head_sha(repo, pr_number)
        # Convert comments to GitHub format with proper positioning
        github_comments = []
        
        # Debug: let's see what we're working with
        print(f"📊 Processing {len(all_comments)} comments", file=sys.stderr)
        
        for c in all_comments:
            numbered_line = c.get("numbered_line", "001")
            file_line_num, is_change_line = extract_file_line_number(numbered_line, diff_text, c["file_path"])
            
            print(f"🔍 Comment: {c['file_path']} line {numbered_line} -> file_line {file_line_num}, is_change: {is_change_line}", file=sys.stderr)
            
            # Only add comments on actual change lines (+ lines only for new code)
            if file_line_num > 0 and is_change_line:
                github_comments.append({
                    "path": c["file_path"],
                    "line": file_line_num,
                    "side": "RIGHT",
                    "body": f"**{c['level'].upper()}**: {c['comment']}"
                })
            else:
                print(f"⚠️ Skipping line {numbered_line} - not a valid change line", file=sys.stderr)
        
        print(f"📤 Sending {len(github_comments)} comments to GitHub", file=sys.stderr)
        github_client.submit_review(repo, pr_number, commit_sha, github_comments)
    except Exception as exc:
        print(f"❌ Błąd podczas wysyłania review na GitHub: {exc}", file=sys.stderr)
    


if __name__ == '__main__':
    main()