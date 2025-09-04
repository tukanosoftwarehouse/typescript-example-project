import { User, CreateUserData, Result } from '../models/types';

/**
 * Service class for managing users
 * Demonstrates basic CRUD operations and TypeScript patterns
 */
export class UserService {
  private users: Map<number, User> = new Map();
  private nextId: number = 1;

  /**
   * Add a new user to the system
   */
  public addUser(user: User): Result<User> {
    try {
      if (this.users.has(user.id)) {
        return {
          success: false,
          error: new Error(`User with id ${user.id} already exists`)
        };
      }

      if (!this.isValidEmail(user.email)) {
        return {
          success: false,
          error: new Error('Invalid email format')
        };
      }

      const newUser: User = {
        ...user,
        isActive: user.isActive ?? true
      };

      this.users.set(user.id, newUser);

      if (user.id >= this.nextId) {
        this.nextId = user.id + 1;
      }

      return {
        success: true,
        data: newUser
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Unknown error')
      };
    }
  }

  /**
   * Create a new user with auto-generated ID
   */
  public createUser(userData: CreateUserData): Result<User> {
    const user: User = {
      id: this.nextId++,
      ...userData,
      createdAt: new Date(),
      isActive: userData.isActive ?? true
    };

    return this.addUser(user);
  }

  /**
   * Get user by ID
   */
  public getUserById(id: number): User | undefined {
    return this.users.get(id);
  }

  /**
   * Get user by email
   */
  public getUserByEmail(email: string): User | undefined {
    for (const user of this.users.values()) {
      if (user.email.toLowerCase() === email.toLowerCase()) {
        return user;
      }
    }
    return undefined;
  }

  /**
   * Get all users
   */
  public getAllUsers(): User[] {
    return Array.from(this.users.values());
  }

  /**
   * Get active users only
   */
  public getActiveUsers(): User[] {
    return this.getAllUsers().filter(user => user.isActive !== false);
  }

  /**
   * Update user information
   */
  public updateUser(id: number, updates: Partial<Omit<User, 'id' | 'createdAt'>>): Result<User> {
    const user = this.users.get(id);
    
    if (!user) {
      return {
        success: false,
        error: new Error(`User with id ${id} not found`)
      };
    }

    if (updates.email && !this.isValidEmail(updates.email)) {
      return {
        success: false,
        error: new Error('Invalid email format')
      };
    }

    const updatedUser: User = {
      ...user,
      ...updates
    };

    this.users.set(id, updatedUser);

    return {
      success: true,
      data: updatedUser
    };
  }

  /**
   * Delete user by ID
   */
  public deleteUser(id: number): boolean {
    return this.users.delete(id);
  }

  /**
   * Get user count
   */
  public getUserCount(): number {
    return this.users.size;
  }

  /**
   * Search users by name (case-insensitive)
   */
  public searchUsersByName(searchTerm: string): User[] {
    const term = searchTerm.toLowerCase();
    return this.getAllUsers().filter(user =>
      user.name.toLowerCase().includes(term)
    );
  }

  /**
   * Validate email format
   */
  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}
