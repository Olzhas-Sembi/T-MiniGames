/**
 * Компонент для демонстрации интеграции с Telegram WebApp
 */
import React, { useEffect, useState } from 'react';
import { useTelegramWebApp } from '../hooks/useTelegramWebApp';

const TelegramIntegrationDemo: React.FC = () => {
  const { isAvailable, user, initData, webApp } = useTelegramWebApp();
  const [stars, setStars] = useState(0);

  useEffect(() => {
    if (isAvailable && user) {
      // Настраиваем главную кнопку
      webApp.setMainButton('Купить звёзды', () => {
        handleBuyStars();
      });

      // Настраиваем кнопку "Назад"
      webApp.setBackButton(() => {
        webApp.close();
      });

      // Получаем баланс пользователя
      fetchUserBalance();
    }

    return () => {
      // Очищаем кнопки при размонтировании
      if (isAvailable) {
        webApp.hideMainButton();
        webApp.hideBackButton();
      }
    };
  }, [isAvailable, user]);

  const fetchUserBalance = async () => {
    if (!user) return;

    try {
      const response = await fetch(`/api/users/${user.id}`, {
        headers: {
          'Authorization': `Bearer ${initData}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setStars(userData.stars_balance || 0);
      }
    } catch (error) {
      console.error('Ошибка получения баланса:', error);
    }
  };

  const handleBuyStars = async () => {
    if (!isAvailable) return;

    // Показываем меню покупки звёзд
    const packages = [
      { stars: 100, price: '$2.00' },
      { stars: 500, price: '$8.00' },
      { stars: 1000, price: '$15.00' }
    ];

    // Можно показать popup с выбором пакета
    const result = await webApp.showPopup(
      'Покупка звёзд',
      'Выберите пакет звёзд для покупки',
      packages.map(pkg => ({
        text: `${pkg.stars} ⭐ - ${pkg.price}`,
        type: 'default'
      }))
    );

    if (result && packages[parseInt(result)]) {
      const selectedPackage = packages[parseInt(result)];
      
      // Отправляем данные о покупке боту
      webApp.sendData({
        action: 'buy_stars',
        package: selectedPackage,
        user_id: user?.id
      });

      // Показываем фидбек
      webApp.hapticFeedback('success');
      await webApp.showAlert(`Запрос на покупку ${selectedPackage.stars} звёзд отправлен!`);
    }
  };

  const handlePlayGame = (gameType: string) => {
    if (!isAvailable) return;

    // Тактильная обратная связь
    webApp.hapticFeedback('light');

    // Отправляем данные о начале игры
    webApp.sendData({
      action: 'start_game',
      game_type: gameType,
      user_id: user?.id
    });
  };

  if (!isAvailable) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-bold mb-4">Запустите в Telegram</h2>
          <p className="text-gray-600">
            Это приложение должно быть запущено через Telegram Bot
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-md mx-auto">
        {/* Приветствие */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-800 mb-2">
              Привет, {user?.first_name}! 👋
            </h1>
            <div className="flex items-center justify-center space-x-2">
              <span className="text-lg">⭐</span>
              <span className="text-xl font-bold text-yellow-600">{stars}</span>
              <span className="text-gray-600">звёзд</span>
            </div>
          </div>
        </div>

        {/* Игры */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">🎮 Игры</h2>
          <div className="space-y-3">
            <button
              onClick={() => handlePlayGame('dice')}
              className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-3 px-4 rounded-xl font-medium hover:from-blue-600 hover:to-blue-700 transition-all"
            >
              🎲 Кости
            </button>
            <button
              onClick={() => handlePlayGame('rps')}
              className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-3 px-4 rounded-xl font-medium hover:from-green-600 hover:to-green-700 transition-all"
            >
              ✂️ Камень-ножницы-бумага
            </button>
          </div>
        </div>

        {/* Статистика */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">📊 Статистика</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">0</div>
              <div className="text-sm text-gray-600">Игр сыграно</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">0</div>
              <div className="text-sm text-gray-600">Побед</div>
            </div>
          </div>
        </div>

        {/* Debug информация (только в разработке) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="bg-gray-100 rounded-xl p-4 mt-6">
            <h3 className="font-bold mb-2">Debug Info:</h3>
            <pre className="text-xs overflow-auto">
              {JSON.stringify({
                isAvailable,
                user,
                initDataLength: initData.length
              }, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default TelegramIntegrationDemo;
