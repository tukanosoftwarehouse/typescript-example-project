/**
 * User interface representing a system user
 */
export interface User {
  id: number;
  name: string;
  email: string;
  createdAt: Date;
  isActive?: boolean;
}

/**
 * Task status enumeration
 */
export enum TaskStatus {
  TODO = 'TODO',
  IN_PROGRESS = 'IN_PROGRESS',
  DONE = 'DONE',
  CANCELLED = 'CANCELLED'
}

/**
 * Task interface representing a work item
 */
export interface Task {
  id: number;
  title: string;
  description: string;
  assigneeId: number;
  status: TaskStatus;
  createdAt: Date;
  updatedAt?: Date;
  dueDate: Date;
  tags?: string[];
}

/**
 * Generic API Response type
 */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[];
}

/**
 * Configuration interface
 */
export interface AppConfig {
  environment: 'development' | 'production' | 'test';
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  database: {
    host: string;
    port: number;
    name: string;
  };
  features: {
    enableLogging: boolean;
    enableMetrics: boolean;
  };
}

/**
 * Pagination parameters
 */
export interface PaginationOptions {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}

/**
 * User creation data (excludes generated fields)
 */
export type CreateUserData = Omit<User, 'id' | 'createdAt'>;

/**
 * Task update data (partial task excluding id and createdAt)
 */
export type UpdateTaskData = Partial<Omit<Task, 'id' | 'createdAt'>>;

/**
 * Log level type
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

/**
 * Event handler function type
 */
export type EventHandler<T = any> = (data: T) => void | Promise<void>;

/**
 * Result type for operations that can fail
 */
export type Result<T, E = Error> = {
  success: true;
  data: T;
} | {
  success: false;
  error: E;
};
