import { UserService } from './services/UserService';
import { TaskManager } from './services/TaskManager';
import { Logger } from './utils/Logger';
import { formatDate, capitalizeString } from './utils/helpers';
import { User, Task, TaskStatus } from './models/types';

/**
 * Main application class that demonstrates TypeScript features
 * and project organization
 */
class Application {
  private userService: UserService;
  private taskManager: TaskManager;
  private logger: Logger;

  constructor() {
    this.userService = new UserService();
    this.taskManager = new TaskManager();
    this.logger = new Logger();
  }

  /**
   * Initialize and run the application
   */
  public async run(): Promise<void> {
    this.logger.info('Starting TypeScript Example Application...');

    try {
      // Create sample users
      const user1: User = {
        id: 1,
        name: 'John Doe',
        email: 'john.doe@example.com',
        createdAt: new Date()
      };

      const user2: User = {
        id: 2,
        name: 'jane smith',
        email: 'jane.smith@example.com',
        createdAt: new Date('2023-01-15')
      };

      // Add users to service
      this.userService.addUser(user1);
      this.userService.addUser(user2);

      // Create sample tasks
      const task1: Task = {
        id: 1,
        title: 'Complete TypeScript project',
        description: 'Build a sample TypeScript application with proper structure',
        assigneeId: 1,
        status: TaskStatus.IN_PROGRESS,
        createdAt: new Date(),
        dueDate: new Date('2024-12-31')
      };

      const task2: Task = {
        id: 2,
        title: 'Write documentation',
        description: 'Create comprehensive documentation for the project',
        assigneeId: 2,
        status: TaskStatus.TODO,
        createdAt: new Date(),
        dueDate: new Date('2024-11-30')
      };

      // Add tasks to manager
      this.taskManager.addTask(task1);
      this.taskManager.addTask(task2);

      // Display application data
      this.displayUsers();
      this.displayTasks();
      this.displayUtilities();

    } catch (error) {
      this.logger.error('Application error:', error);
    }
  }

  private displayUsers(): void {
    this.logger.info('\n=== Users ===');
    const users = this.userService.getAllUsers();
    users.forEach(user => {
      const formattedName = capitalizeString(user.name);
      const joinDate = formatDate(user.createdAt);
      this.logger.info(`${formattedName} (${user.email}) - Joined: ${joinDate}`);
    });
  }

  private displayTasks(): void {
    this.logger.info('\n=== Tasks ===');
    const tasks = this.taskManager.getAllTasks();
    tasks.forEach(task => {
      const assignee = this.userService.getUserById(task.assigneeId);
      const dueDate = formatDate(task.dueDate);
      this.logger.info(`[${task.status}] ${task.title} - Assigned to: ${assignee?.name || 'Unknown'} - Due: ${dueDate}`);
    });
  }

  private displayUtilities(): void {
    this.logger.info('\n=== Utility Examples ===');
    this.logger.info(`Current date formatted: ${formatDate(new Date())}`);
    this.logger.info(`Capitalized text: ${capitalizeString('hello world from typescript')}`);
  }
}

// Application entry point
const app = new Application();
app.run().catch(console.error);
