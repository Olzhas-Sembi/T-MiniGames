/**
 * Telegram WebApp API интеграция
 * Обеспечивает связь между Mini App и Telegram
 */

interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: {
      id: number;
      first_name: string;
      last_name?: string;
      username?: string;
      language_code?: string;
      is_premium?: boolean;
    };
    auth_date: number;
    hash: string;
  };
  version: string;
  platform: string;
  colorScheme: 'light' | 'dark';
  themeParams: {
    bg_color?: string;
    text_color?: string;
    hint_color?: string;
    link_color?: string;
    button_color?: string;
    button_text_color?: string;
  };
  isExpanded: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  MainButton: {
    text: string;
    color: string;
    textColor: string;
    isVisible: boolean;
    isProgressVisible: boolean;
    isActive: boolean;
    setText: (text: string) => void;
    onClick: (callback: () => void) => void;
    show: () => void;
    hide: () => void;
    enable: () => void;
    disable: () => void;
    showProgress: (leaveActive?: boolean) => void;
    hideProgress: () => void;
  };
  BackButton: {
    isVisible: boolean;
    onClick: (callback: () => void) => void;
    show: () => void;
    hide: () => void;
  };
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
    selectionChanged: () => void;
  };
  ready: () => void;
  expand: () => void;
  close: () => void;
  sendData: (data: string) => void;
  showPopup: (params: {
    title?: string;
    message: string;
    buttons?: Array<{
      id?: string;
      type?: 'default' | 'ok' | 'close' | 'cancel' | 'destructive';
      text: string;
    }>;
  }, callback?: (buttonId: string) => void) => void;
  showAlert: (message: string, callback?: () => void) => void;
  showConfirm: (message: string, callback?: (confirmed: boolean) => void) => void;
  showScanQrPopup: (params: {
    text?: string;
  }, callback?: (text: string) => void) => void;
  closeScanQrPopup: () => void;
  onEvent: (eventType: string, eventHandler: () => void) => void;
  offEvent: (eventType: string, eventHandler: () => void) => void;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

class TelegramWebAppService {
  private webApp: TelegramWebApp | null = null;
  private isInitialized = false;

  constructor() {
    this.initWebApp();
  }

  /**
   * Инициализация Telegram WebApp
   */
  private initWebApp(): void {
    if (typeof window === 'undefined') {
      console.warn('TelegramWebApp: не запущено в браузере');
      return;
    }

    if (!window.Telegram?.WebApp) {
      console.warn('TelegramWebApp: Telegram WebApp API недоступен');
      return;
    }

    this.webApp = window.Telegram.WebApp;
    this.webApp.ready();
    this.webApp.expand();
    this.isInitialized = true;

    console.log('TelegramWebApp инициализирован:', {
      version: this.webApp.version,
      platform: this.webApp.platform,
      user: this.webApp.initDataUnsafe.user
    });

    // Настройка темы
    this.setupTheme();
  }

  /**
   * Проверка доступности WebApp
   */
  isAvailable(): boolean {
    return this.isInitialized && this.webApp !== null;
  }

  /**
   * Получение данных пользователя
   */
  getUser() {
    if (!this.isAvailable()) {
      return null;
    }
    return this.webApp!.initDataUnsafe.user || null;
  }

  /**
   * Получение init данных для отправки на сервер
   */
  getInitData(): string {
    if (!this.isAvailable()) {
      return '';
    }
    return this.webApp!.initData || '';
  }

  /**
   * Настройка главной кнопки
   */
  setMainButton(text: string, onClick: () => void): void {
    if (!this.isAvailable()) {
      console.warn('TelegramWebApp: MainButton недоступна');
      return;
    }

    const mainButton = this.webApp!.MainButton;
    mainButton.setText(text);
    mainButton.onClick(onClick);
    mainButton.show();
    mainButton.enable();
  }

  /**
   * Скрытие главной кнопки
   */
  hideMainButton(): void {
    if (!this.isAvailable()) return;
    this.webApp!.MainButton.hide();
  }

  /**
   * Настройка кнопки "Назад"
   */
  setBackButton(onClick: () => void): void {
    if (!this.isAvailable()) {
      console.warn('TelegramWebApp: BackButton недоступна');
      return;
    }

    const backButton = this.webApp!.BackButton;
    backButton.onClick(onClick);
    backButton.show();
  }

  /**
   * Скрытие кнопки "Назад"
   */
  hideBackButton(): void {
    if (!this.isAvailable()) return;
    this.webApp!.BackButton.hide();
  }

  /**
   * Вибрация (тактильная обратная связь)
   */
  hapticFeedback(type: 'light' | 'medium' | 'heavy' | 'success' | 'error' | 'warning' | 'selection'): void {
    if (!this.isAvailable()) return;

    const haptic = this.webApp!.HapticFeedback;
    
    switch (type) {
      case 'light':
      case 'medium':
      case 'heavy':
        haptic.impactOccurred(type);
        break;
      case 'success':
      case 'error':
      case 'warning':
        haptic.notificationOccurred(type);
        break;
      case 'selection':
        haptic.selectionChanged();
        break;
    }
  }

  /**
   * Показ всплывающего окна
   */
  showPopup(
    title: string,
    message: string,
    buttons: Array<{ text: string; type?: 'default' | 'destructive' }> = [{ text: 'OK' }]
  ): Promise<string> {
    if (!this.isAvailable()) {
      return Promise.resolve('');
    }

    return new Promise((resolve) => {
      this.webApp!.showPopup(
        {
          title,
          message,
          buttons: buttons.map((btn, index) => ({
            id: index.toString(),
            text: btn.text,
            type: btn.type || 'default'
          }))
        },
        (buttonId) => {
          resolve(buttonId);
        }
      );
    });
  }

  /**
   * Показ алерта
   */
  showAlert(message: string): Promise<void> {
    if (!this.isAvailable()) {
      return Promise.resolve();
    }

    return new Promise((resolve) => {
      this.webApp!.showAlert(message, () => {
        resolve();
      });
    });
  }

  /**
   * Показ подтверждения
   */
  showConfirm(message: string): Promise<boolean> {
    if (!this.isAvailable()) {
      return Promise.resolve(false);
    }

    return new Promise((resolve) => {
      this.webApp!.showConfirm(message, (confirmed) => {
        resolve(confirmed);
      });
    });
  }

  /**
   * Закрытие WebApp
   */
  close(): void {
    if (!this.isAvailable()) return;
    this.webApp!.close();
  }

  /**
   * Отправка данных боту
   */
  sendData(data: any): void {
    if (!this.isAvailable()) {
      console.warn('TelegramWebApp: отправка данных недоступна');
      return;
    }
    
    const dataString = typeof data === 'string' ? data : JSON.stringify(data);
    this.webApp!.sendData(dataString);
  }

  /**
   * Настройка темы приложения
   */
  private setupTheme(): void {
    if (!this.isAvailable()) return;

    const themeParams = this.webApp!.themeParams;
    const root = document.documentElement;

    // Устанавливаем CSS переменные для темы
    if (themeParams.bg_color) {
      root.style.setProperty('--tg-bg-color', themeParams.bg_color);
    }
    if (themeParams.text_color) {
      root.style.setProperty('--tg-text-color', themeParams.text_color);
    }
    if (themeParams.hint_color) {
      root.style.setProperty('--tg-hint-color', themeParams.hint_color);
    }
    if (themeParams.link_color) {
      root.style.setProperty('--tg-link-color', themeParams.link_color);
    }
    if (themeParams.button_color) {
      root.style.setProperty('--tg-button-color', themeParams.button_color);
    }
    if (themeParams.button_text_color) {
      root.style.setProperty('--tg-button-text-color', themeParams.button_text_color);
    }

    // Устанавливаем класс темы
    document.body.classList.add(this.webApp!.colorScheme === 'dark' ? 'tg-dark' : 'tg-light');
  }

  /**
   * Получение параметров темы
   */
  getThemeParams() {
    if (!this.isAvailable()) return {};
    return this.webApp!.themeParams;
  }

  /**
   * Проверка, запущено ли в Telegram
   */
  static isTelegramWebApp(): boolean {
    return typeof window !== 'undefined' && !!window.Telegram?.WebApp;
  }
}

// Создаем глобальный экземпляр сервиса
export const telegramWebApp = new TelegramWebAppService();

// Экспортируем также класс для создания дополнительных экземпляров
export { TelegramWebAppService };

// Типы для TypeScript
export type { TelegramWebApp };
