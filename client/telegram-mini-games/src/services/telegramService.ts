// Импортируем типы из telegramWebApp
import type { TelegramWebApp } from './telegramWebApp';

// Telegram WebApp API типы
interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
  photo_url?: string;
}

class TelegramService {
  private webApp: TelegramWebApp | null = null;
  private isInitialized = false;

  constructor() {
    this.init();
  }

  init(): void {
    try {
      // Проверяем доступность Telegram WebApp
      if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
        this.webApp = window.Telegram.WebApp;
        this.webApp.ready();
        this.webApp.expand();
        this.isInitialized = true;
        console.log('Telegram WebApp initialized successfully');
      } else {
        console.warn('Telegram WebApp not available');
      }
    } catch (error) {
      console.error('Error initializing Telegram WebApp:', error);
    }
  }

  isInTelegram(): boolean {
    if (!this.webApp) return false;
    
    // Проверяем наличие initData
    if (!this.webApp.initData || this.webApp.initData.length === 0) {
      return false;
    }
    
    // Проверяем наличие пользователя
    if (!this.webApp.initDataUnsafe?.user) {
      return false;
    }
    
    // Проверяем платформу
    const platform = this.webApp.platform;
    const validPlatforms = ['ios', 'android', 'macos', 'tdesktop', 'web'];
    
    return validPlatforms.includes(platform);
  }

  getUser(): TelegramUser | null {
    if (!this.webApp?.initDataUnsafe?.user) {
      return null;
    }
    return this.webApp.initDataUnsafe.user;
  }

  getUserId(): number | null {
    const user = this.getUser();
    return user?.id || null;
  }

  getInitData(): string {
    return this.webApp?.initData || '';
  }

  showAlert(message: string): void {
    if (this.webApp) {
      this.webApp.showAlert(message);
    } else {
      alert(message);
    }
  }

  showConfirm(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.webApp) {
        this.webApp.showConfirm(message, resolve);
      } else {
        resolve(confirm(message));
      }
    });
  }

  close(): void {
    if (this.webApp) {
      this.webApp.close();
    }
  }

  sendData(data: string): void {
    if (this.webApp) {
      this.webApp.sendData(data);
    }
  }

  getTheme(): 'light' | 'dark' {
    return this.webApp?.colorScheme || 'dark';
  }

  isReady(): boolean {
    return this.isInitialized && this.webApp !== null;
  }
}

// Создаем единственный экземпляр сервиса
const telegramService = new TelegramService();

// Экспортируем и класс, и экземпляр для обратной совместимости
export { TelegramService, telegramService };
export default telegramService;
