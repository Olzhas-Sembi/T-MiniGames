/**
 * Хук для работы с Telegram WebApp
 */
import { useEffect, useState } from 'react';
import { telegramWebApp } from '../services/telegramWebApp';

interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
}

export const useTelegramWebApp = () => {
  const [isAvailable, setIsAvailable] = useState(false);
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [initData, setInitData] = useState<string>('');

  useEffect(() => {
    // Проверяем доступность WebApp
    const available = telegramWebApp.isAvailable();
    setIsAvailable(available);

    if (available) {
      // Получаем данные пользователя
      const telegramUser = telegramWebApp.getUser();
      setUser(telegramUser);

      // Получаем init данные
      const initDataString = telegramWebApp.getInitData();
      setInitData(initDataString);
    }
  }, []);

  return {
    isAvailable,
    user,
    initData,
    webApp: telegramWebApp
  };
};
