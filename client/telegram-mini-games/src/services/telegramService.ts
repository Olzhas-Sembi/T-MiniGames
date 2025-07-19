// Telegram WebApp API интеграция
declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
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
          chat?: any;
          auth_date: number;
          hash: string;
        };
        version: string;
        platform: string;
        colorScheme: 'light' | 'dark';
        themeParams: {
          link_color?: string;
          button_color?: string;
          button_text_color?: string;
          secondary_bg_color?: string;
          hint_color?: string;
          bg_color?: string;
          text_color?: string;
        };
        isExpanded: boolean;
        viewportHeight: number;
        viewportStableHeight: number;
        headerColor: string;
        backgroundColor: string;
        BackButton: {
          isVisible: boolean;
          onClick: (callback: () => void) => void;
          offClick: (callback: () => void) => void;
          show: () => void;
          hide: () => void;
        };
        MainButton: {
          text: string;
          color: string;
          textColor: string;
          isVisible: boolean;
          isProgressVisible: boolean;
          isActive: boolean;
          setText: (text: string) => void;
          onClick: (callback: () => void) => void;
          offClick: (callback: () => void) => void;
          show: () => void;
          hide: () => void;
          enable: () => void;
          disable: () => void;
          showProgress: (leaveActive?: boolean) => void;
          hideProgress: () => void;
        };
        HapticFeedback: {
          impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
          notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
          selectionChanged: () => void;
        };
        CloudStorage: {
          setItem: (key: string, value: string, callback?: (error: Error | null, success: boolean) => void) => void;
          getItem: (key: string, callback: (error: Error | null, value: string | null) => void) => void;
          getItems: (keys: string[], callback: (error: Error | null, values: Record<string, string>) => void) => void;
          removeItem: (key: string, callback?: (error: Error | null, success: boolean) => void) => void;
          removeItems: (keys: string[], callback?: (error: Error | null, success: boolean) => void) => void;
          getKeys: (callback: (error: Error | null, keys: string[]) => void) => void;
        };
        ready: () => void;
        expand: () => void;
        close: () => void;
        sendData: (data: string) => void;
        openLink: (url: string, options?: { try_instant_view?: boolean }) => void;
        openTelegramLink: (url: string) => void;
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
        onEvent: (eventType: string, eventHandler: Function) => void;
        offEvent: (eventType: string, eventHandler: Function) => void;
      };
    };
  }
}

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
}

export class TelegramService {
  private static instance: TelegramService;
  
  public static getInstance(): TelegramService {
    if (!TelegramService.instance) {
      TelegramService.instance = new TelegramService();
    }
    return TelegramService.instance;
  }

  /**
   * Проверяет, запущено ли приложение в Telegram
   */
  public isInTelegram(): boolean {
    return typeof window !== 'undefined' && !!window.Telegram?.WebApp;
  }

  /**
   * Инициализация Telegram WebApp
   */
  public init(): void {
    if (this.isInTelegram()) {
      window.Telegram!.WebApp!.ready();
      window.Telegram!.WebApp!.expand();
      
      // Настройка темы
      this.applyTheme();
      
      console.log('Telegram WebApp initialized');
    }
  }

  /**
   * Получить данные пользователя Telegram
   */
  public getUser(): TelegramUser | null {
    if (!this.isInTelegram()) return null;
    
    const user = window.Telegram!.WebApp!.initDataUnsafe.user;
    return user || null;
  }

  /**
   * Получить параметры запуска (например, room_id)
   */
  public getStartParam(): string | null {
    if (!this.isInTelegram()) {
      // Для разработки проверяем URL параметры
      const urlParams = new URLSearchParams(window.location.search);
      return urlParams.get('room_id');
    }
    
    const initData = window.Telegram!.WebApp!.initDataUnsafe;
    return (initData as any).start_param || null;
  }

  /**
   * Применить тему Telegram к приложению
   */
  private applyTheme(): void {
    if (!this.isInTelegram()) return;
    
    const themeParams = window.Telegram!.WebApp!.themeParams;
    const isDark = window.Telegram!.WebApp!.colorScheme === 'dark';
    
    // Обновляем CSS переменные
    const root = document.documentElement;
    
    if (themeParams.bg_color) {
      root.style.setProperty('--tg-bg-color', themeParams.bg_color);
    }
    
    if (themeParams.text_color) {
      root.style.setProperty('--tg-text-color', themeParams.text_color);
    }
    
    if (themeParams.button_color) {
      root.style.setProperty('--tg-button-color', themeParams.button_color);
    }
    
    if (themeParams.button_text_color) {
      root.style.setProperty('--tg-button-text-color', themeParams.button_text_color);
    }
    
    // Добавляем класс для темной темы
    if (isDark) {
      document.body.classList.add('telegram-dark');
    } else {
      document.body.classList.add('telegram-light');
    }
  }

  /**
   * Показать главную кнопку Telegram
   */
  public showMainButton(text: string, onClick: () => void): void {
    if (!this.isInTelegram()) return;
    
    const mainButton = window.Telegram!.WebApp!.MainButton;
    mainButton.setText(text);
    mainButton.onClick(onClick);
    mainButton.show();
  }

  /**
   * Скрыть главную кнопку Telegram
   */
  public hideMainButton(): void {
    if (!this.isInTelegram()) return;
    
    window.Telegram!.WebApp!.MainButton.hide();
  }

  /**
   * Показать кнопку "Назад"
   */
  public showBackButton(onClick: () => void): void {
    if (!this.isInTelegram()) return;
    
    const backButton = window.Telegram!.WebApp!.BackButton;
    backButton.onClick(onClick);
    backButton.show();
  }

  /**
   * Скрыть кнопку "Назад"
   */
  public hideBackButton(): void {
    if (!this.isInTelegram()) return;
    
    window.Telegram!.WebApp!.BackButton.hide();
  }

  /**
   * Тактильная обратная связь
   */
  public hapticFeedback(type: 'light' | 'medium' | 'heavy' | 'success' | 'error' | 'warning' = 'light'): void {
    if (!this.isInTelegram()) return;
    
    const haptic = window.Telegram!.WebApp!.HapticFeedback;
    
    if (type === 'success' || type === 'error' || type === 'warning') {
      haptic.notificationOccurred(type);
    } else {
      haptic.impactOccurred(type);
    }
  }

  /**
   * Поделиться ссылкой на игру
   */
  public shareGameLink(roomId: string): void {
    const gameUrl = `https://t.me/your_bot?startapp=join_${roomId}`;
    
    if (this.isInTelegram()) {
      window.Telegram!.WebApp!.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(gameUrl)}&text=${encodeURIComponent('Присоединяйся к игре!')}`);
    } else {
      // Для разработки копируем в буфер обмена
      navigator.clipboard.writeText(gameUrl).then(() => {
        alert('Ссылка скопирована в буфер обмена!');
      });
    }
  }

  /**
   * Показать уведомление
   */
  public showAlert(message: string): Promise<void> {
    return new Promise((resolve) => {
      if (this.isInTelegram()) {
        window.Telegram!.WebApp!.showAlert(message, () => resolve());
      } else {
        alert(message);
        resolve();
      }
    });
  }

  /**
   * Показать подтверждение
   */
  public showConfirm(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.isInTelegram()) {
        window.Telegram!.WebApp!.showConfirm(message, (confirmed) => resolve(confirmed));
      } else {
        resolve(confirm(message));
      }
    });
  }

  /**
   * Закрыть приложение
   */
  public close(): void {
    if (this.isInTelegram()) {
      window.Telegram!.WebApp!.close();
    } else {
      window.close();
    }
  }

  /**
   * Генерация уникального ID игрока на основе Telegram данных
   */
  public getPlayerId(): string {
    const user = this.getUser();
    if (user) {
      return `tg_${user.id}`;
    }
    
    // Для разработки генерируем случайный ID
    let playerId = localStorage.getItem('dev_player_id');
    if (!playerId) {
      playerId = `dev_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('dev_player_id', playerId);
    }
    return playerId;
  }

  /**
   * Получить username игрока
   */
  public getUsername(): string {
    const user = this.getUser();
    if (user) {
      return user.username || user.first_name || `User${user.id}`;
    }
    
    // Для разработки
    let username = localStorage.getItem('dev_username');
    if (!username) {
      username = `TestUser${Math.floor(Math.random() * 1000)}`;
      localStorage.setItem('dev_username', username);
    }
    return username;
  }

  /**
   * Получить Telegram ID
   */
  public getTelegramId(): string {
    const user = this.getUser();
    if (user) {
      return user.id.toString();
    }
    
    // Для разработки
    let telegramId = localStorage.getItem('dev_telegram_id');
    if (!telegramId) {
      telegramId = Math.floor(Math.random() * 1000000).toString();
      localStorage.setItem('dev_telegram_id', telegramId);
    }
    return telegramId;
  }
}

export default TelegramService.getInstance();
