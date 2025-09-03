#!/usr/bin/env python3

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
import os
import yaml
import openai
import requests
from typing import List
from pathlib import Path


@dataclass
class LLMConfig:
    """Konfiguracja dla providera LLM"""
    model: str
    temperature: float
    max_tokens: int
    endpoint: str
    api_key_env: str
    timeout_seconds: int = 120
    retry_attempts: int = 3


class LLMProvider(ABC):
    """Abstrakcyjny interfejs dla providerów LLM"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = os.getenv(config.api_key_env)
        if not self.api_key and config.api_key_env != "OPENAI_API_KEY":
            raise ValueError(f"Brak klucza API w zmiennej środowiskowej: {config.api_key_env}")
    
    @abstractmethod
    def review_code(self, diff_chunk: str, system_prompt: str) -> List[Dict[str, Any]]:
        """Wykonaj review kodu i zwróć listę komentarzy"""
        pass
    
    def _parse_response(self, raw_response: str) -> List[Dict[str, Any]]:
        """Parsuj surową odpowiedź z modelu do listy komentarzy"""
        # Domyślna implementacja - może być nadpisana przez konkretne providery
        return json.loads(raw_response)
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Zwróć informacje o modelu"""
        pass


class OpenAIProvider(LLMProvider):
    """Provider dla OpenAI GPT modeli"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = openai.OpenAI(
            base_url=config.endpoint.rstrip('/'),
            api_key=self.api_key or 'dummy'
        )
    
    def review_code(self, diff_chunk: str, system_prompt: str) -> List[Dict[str, Any]]:
        """Wykonaj review kodu używając OpenAI API"""
        user_prompt = f"""Oceń poniższy diff w formacie unified diff.\n
        ```diff
        {diff_chunk}
        ```"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            
            if not response or not response.choices:
                raise ValueError('Invalid response from OpenAI')
            
            content = response.choices[0].message.content
            if content is None:
                raise ValueError('OpenAI response message content is None')
            
            return self._parse_response(content.strip())
            
        except Exception as e:
            raise RuntimeError(f'Error during OpenAI request: {e}')
    
    def _parse_response(self, raw_response: str) -> List[Dict[str, Any]]:
        """Parsuj odpowiedź OpenAI - zwykle czyste JSON"""
        try:
            # OpenAI zwykle zwraca czyste JSON
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # Fallback - spróbuj usunąć markdown bloki
            cleaned = raw_response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned.split('\n', 1)[-1]
            if cleaned.endswith('```'):
                cleaned = cleaned.rsplit('```', 1)[0]
            return json.loads(cleaned)
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "openai",
            "model": self.config.model,
            "endpoint": self.config.endpoint,
            "max_tokens": self.config.max_tokens
        }


class LocalLLMProvider(LLMProvider):
    """Provider dla lokalnych modeli (LM Studio, Ollama) z OpenAI compatible API"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = openai.OpenAI(
            base_url=config.endpoint.rstrip('/'),
            api_key=self.api_key or 'dummy'
        )
    
    def review_code(self, diff_chunk: str, system_prompt: str) -> List[Dict[str, Any]]:
        """Wykonaj review kodu używając lokalnego modelu"""
        user_prompt = f"""Oceń poniższy diff w formacie unified diff.\n
        ```diff
        {diff_chunk}
        ```"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            
            if not response or not response.choices:
                raise ValueError('Invalid response from local LLM')
            
            content = response.choices[0].message.content
            if content is None:
                raise ValueError('Local LLM response message content is None')
            
            return self._parse_response(content.strip())
            
        except Exception as e:
            raise RuntimeError(f'Error during local LLM request: {e}')
    
    def _parse_response(self, raw_response: str) -> List[Dict[str, Any]]:
        """Parsuj odpowiedź lokalnego modelu - często zawiera markdown bloki"""
        try:
            cleaned = raw_response.strip()
            # Lokalne modele często opakowują JSON w markdown bloki
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                # Usuń pierwszą linię z ```json lub ```
                cleaned = '\n'.join(lines[1:])
                if cleaned.endswith('```'):
                    cleaned = cleaned.rsplit('```', 1)[0]
            
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Jeśli parsowanie nie udało się, spróbuj znaleźć JSON w tekście
            import re
            json_match = re.search(r'\[.*\]', raw_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise RuntimeError(f'Cannot parse local LLM response as JSON: {e}')
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "local",
            "model": self.config.model,
            "endpoint": self.config.endpoint,
            "max_tokens": self.config.max_tokens
        }


class AnthropicProvider(LLMProvider):
    """Provider dla Anthropic Claude modeli"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.endpoint.rstrip('/')
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def review_code(self, diff_chunk: str, system_prompt: str) -> List[Dict[str, Any]]:
        """Wykonaj review kodu używając Anthropic Claude API"""
        user_prompt = f"""Oceń poniższy diff w formacie unified diff.\n
        ```diff
        {diff_chunk}
        ```"""
        
        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/messages",
                headers=self.headers,
                json=payload,
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            data = response.json()
            if not data.get('content') or not data['content'][0].get('text'):
                raise ValueError('Invalid response from Anthropic')
            
            return self._parse_response(data['content'][0]['text'].strip())
            
        except Exception as e:
            raise RuntimeError(f'Error during Anthropic request: {e}')
    
    def _parse_response(self, raw_response: str) -> List[Dict[str, Any]]:
        """Parsuj odpowiedź Anthropic - może zawierać dodatkowy tekst przed/po JSON"""
        try:
            # Claude często dodaje wyjaśnienia przed/po JSON
            import re
            # Znajdź JSON array w odpowiedzi
            json_match = re.search(r'\[.*?\]', raw_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Jeśli nie znaleziono, spróbuj parsować całość
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # Fallback - usuń markdown bloki jeśli są
            cleaned = raw_response.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('\n', 1)[-1]
            if cleaned.endswith('```'):
                cleaned = cleaned.rsplit('```', 1)[0]
            return json.loads(cleaned)
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "anthropic",
            "model": self.config.model,
            "endpoint": self.config.endpoint,
            "max_tokens": self.config.max_tokens
        }


class LLMProviderFactory:
    """Factory do tworzenia providerów LLM"""
    
    PROVIDER_CLASSES = {
        'openrouter_gpt4.1': OpenAIProvider,
        'openai': OpenAIProvider,
        'openai_gpt35': OpenAIProvider,
        'local_lmstudio': LocalLLMProvider,
        'anthropic': AnthropicProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, config: LLMConfig) -> LLMProvider:
        """Utwórz providera na podstawie nazwy"""
        if provider_name not in cls.PROVIDER_CLASSES:
            raise ValueError(f"Nieznany provider: {provider_name}. Dostępne: {list(cls.PROVIDER_CLASSES.keys())}")
        
        provider_class = cls.PROVIDER_CLASSES[provider_name]
        return provider_class(config)
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Załaduj konfigurację z pliku YAML"""
        if config_path is None:
            # Domyślna ścieżka względem tego pliku
            config_path = Path(__file__).parent / "llm_config.yml"
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Plik konfiguracyjny nie istnieje: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @classmethod
    def create_from_config(cls, config_path: Optional[str] = None, provider_override: Optional[str] = None) -> LLMProvider:
        config_data = cls.load_config(config_path)
        
        # Wybierz aktywnego providera
        env_provider = os.getenv('LLM_PROVIDER')
        config_provider = config_data.get('active_provider', 'openai')
        active_provider = (
            provider_override or 
            env_provider or 
            config_provider
        )
        
        if active_provider not in config_data['providers']:
            raise ValueError(f"Provider '{active_provider}' nie istnieje w konfiguracji")
        
        provider_config_dict = config_data['providers'][active_provider]
        global_settings = config_data.get('global_settings', {})
        
        # Utwórz obiekt konfiguracji
        llm_config = LLMConfig(
            model=provider_config_dict['model'],
            temperature=provider_config_dict['temperature'],
            max_tokens=provider_config_dict['max_tokens'],
            endpoint=provider_config_dict['endpoint'],
            api_key_env=provider_config_dict['api_key_env'],
            timeout_seconds=global_settings.get('timeout_seconds', 120),
            retry_attempts=global_settings.get('retry_attempts', 3)
        )
        
        return cls.create_provider(active_provider, llm_config)
