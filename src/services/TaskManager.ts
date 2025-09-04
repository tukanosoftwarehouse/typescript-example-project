import { Task, TaskStatus, UpdateTaskData, Result } from '../models/types';

/**
 * Service class for managing tasks
 * Demonstrates task lifecycle management and filtering
 */
export class TaskManager {
  private tasks: Map<number, Task> = new Map();
  private nextId: number = 1;

  /**
   * Add a new task
   */
  public addTask(task: Task): Result<Task> {
    try {
      if (this.tasks.has(task.id)) {
        return {
          success: false,
          error: new Error(`Task with id ${task.id} already exists`)
        };
      }

      if (!task.title.trim()) {
        return {
          success: false,
          error: new Error('Task title cannot be empty')
        };
      }

      const newTask: Task = {
        ...task,
        updatedAt: new Date()
      };

      this.tasks.set(task.id, newTask);

      if (task.id >= this.nextId) {
        this.nextId = task.id + 1;
      }

      return {
        success: true,
        data: newTask
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Unknown error')
      };
    }
  }

  /**
   * Create a new task with auto-generated ID
   */
  public createTask(
    title: string,
    description: string,
    assigneeId: number,
    dueDate: Date
  ): Result<Task> {
    const task: Task = {
      id: this.nextId++,
      title,
      description,
      assigneeId,
      status: TaskStatus.TODO,
      createdAt: new Date(),
      dueDate,
      tags: []
    };

    return this.addTask(task);
  }

  /**
   * Get task by ID
   */
  public getTaskById(id: number): Task | undefined {
    return this.tasks.get(id);
  }

  /**
   * Get all tasks
   */
  public getAllTasks(): Task[] {
    return Array.from(this.tasks.values());
  }

  /**
   * Get tasks by status
   */
  public getTasksByStatus(status: TaskStatus): Task[] {
    return this.getAllTasks().filter(task => task.status === status);
  }

  /**
   * Get tasks assigned to a specific user
   */
  public getTasksByAssignee(assigneeId: number): Task[] {
    return this.getAllTasks().filter(task => task.assigneeId === assigneeId);
  }

  /**
   * Get overdue tasks
   */
  public getOverdueTasks(): Task[] {
    const now = new Date();
    return this.getAllTasks().filter(task => 
      task.dueDate < now && task.status !== TaskStatus.DONE
    );
  }

  /**
   * Update task
   */
  public updateTask(id: number, updates: UpdateTaskData): Result<Task> {
    const task = this.tasks.get(id);
    
    if (!task) {
      return {
        success: false,
        error: new Error(`Task with id ${id} not found`)
      };
    }

    if (updates.title !== undefined && !updates.title.trim()) {
      return {
        success: false,
        error: new Error('Task title cannot be empty')
      };
    }

    const updatedTask: Task = {
      ...task,
      ...updates,
      updatedAt: new Date()
    };

    this.tasks.set(id, updatedTask);

    return {
      success: true,
      data: updatedTask
    };
  }

  /**
   * Update task status
   */
  public updateTaskStatus(id: number, status: TaskStatus): Result<Task> {
    return this.updateTask(id, { status });
  }

  /**
   * Add tag to task
   */
  public addTagToTask(id: number, tag: string): Result<Task> {
    const task = this.tasks.get(id);
    
    if (!task) {
      return {
        success: false,
        error: new Error(`Task with id ${id} not found`)
      };
    }

    const tags = task.tags || [];
    if (!tags.includes(tag)) {
      tags.push(tag);
      return this.updateTask(id, { tags });
    }

    return {
      success: true,
      data: task
    };
  }

  /**
   * Remove tag from task
   */
  public removeTagFromTask(id: number, tag: string): Result<Task> {
    const task = this.tasks.get(id);
    
    if (!task) {
      return {
        success: false,
        error: new Error(`Task with id ${id} not found`)
      };
    }

    const tags = (task.tags || []).filter(t => t !== tag);
    return this.updateTask(id, { tags });
  }

  /**
   * Delete task
   */
  public deleteTask(id: number): boolean {
    return this.tasks.delete(id);
  }

  /**
   * Get task statistics
   */
  public getTaskStatistics(): Record<TaskStatus, number> {
    const stats: Record<TaskStatus, number> = {
      [TaskStatus.TODO]: 0,
      [TaskStatus.IN_PROGRESS]: 0,
      [TaskStatus.DONE]: 0,
      [TaskStatus.CANCELLED]: 0
    };

    for (const task of this.tasks.values()) {
      stats[task.status]++;
    }

    return stats;
  }

  /**
   * Search tasks by title or description
   */
  public searchTasks(searchTerm: string): Task[] {
    const term = searchTerm.toLowerCase();
    return this.getAllTasks().filter(task =>
      task.title.toLowerCase().includes(term) ||
      task.description.toLowerCase().includes(term)
    );
  }
}
