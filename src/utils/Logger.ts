import { LogLevel } from '../models/types';

/**
 * Simple logger utility class
 * Demonstrates TypeScript class patterns and log levels
 */
export class Logger {
  private logLevel: LogLevel;
  private enableTimestamp: boolean;

  constructor(logLevel: LogLevel = 'info', enableTimestamp: boolean = true) {
    this.logLevel = logLevel;
    this.enableTimestamp = enableTimestamp;
  }

  /**
   * Log debug message
   */
  public debug(message: string, ...args: any[]): void {
    if (this.shouldLog('debug')) {
      this.log('DEBUG', message, ...args);
    }
  }

  /**
   * Log info message
   */
  public info(message: string, ...args: any[]): void {
    if (this.shouldLog('info')) {
      this.log('INFO', message, ...args);
    }
  }

  /**
   * Log warning message
   */
  public warn(message: string, ...args: any[]): void {
    if (this.shouldLog('warn')) {
      this.log('WARN', message, ...args);
    }
  }

  /**
   * Log error message
   */
  public error(message: string, ...args: any[]): void {
    if (this.shouldLog('error')) {
      this.log('ERROR', message, ...args);
    }
  }

  /**
   * Set log level
   */
  public setLogLevel(level: LogLevel): void {
    this.logLevel = level;
  }

  /**
   * Get current log level
   */
  public getLogLevel(): LogLevel {
    return this.logLevel;
  }

  /**
   * Enable or disable timestamps
   */
  public setTimestamp(enabled: boolean): void {
    this.enableTimestamp = enabled;
  }

  /**
   * Check if message should be logged based on current log level
   */
  private shouldLog(messageLevel: LogLevel): boolean {
    const levels: Record<LogLevel, number> = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3
    };

    return levels[messageLevel] >= levels[this.logLevel];
  }

  /**
   * Internal log method
   */
  private log(level: string, message: string, ...args: any[]): void {
    const timestamp = this.enableTimestamp ? this.getTimestamp() : '';
    const prefix = timestamp ? `[${timestamp}] [${level}]` : `[${level}]`;
    
    // Use appropriate console method based on level
    switch (level) {
      case 'DEBUG':
        console.debug(`${prefix} ${message}`, ...args);
        break;
      case 'INFO':
        console.info(`${prefix} ${message}`, ...args);
        break;
      case 'WARN':
        console.warn(`${prefix} ${message}`, ...args);
        break;
      case 'ERROR':
        console.error(`${prefix} ${message}`, ...args);
        break;
      default:
        console.log(`${prefix} ${message}`, ...args);
    }
  }

  /**
   * Get formatted timestamp
   */
  private getTimestamp(): string {
    return new Date().toISOString();
  }
}
