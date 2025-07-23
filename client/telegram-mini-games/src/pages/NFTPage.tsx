import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Star, Package, Trophy, Sparkles } from 'lucide-react';
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import NFTCollection from '../components/NFTCollection';
import PaymentModal from '../components/PaymentModal';
import { TelegramService } from '../services/telegramService';
import { baseURL } from '../config';

const NFTPage: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [userBalance, setUserBalance] = useState(0);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initializePage();
  }, []);

  const initializePage = async () => {
    try {
      // Получаем данные пользователя из Telegram
      const telegramService = new TelegramService();
      const userData = telegramService.getUser();
      setUser(userData);

      if (userData?.id) {
        // Загружаем баланс пользователя
        await loadUserBalance(userData.id.toString());
      }
    } catch (error) {
      console.error('Error initializing NFT page:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserBalance = async (userId: string) => {
    try {
      const response = await fetch(`${baseURL}/api/users/${userId}`);
      if (response.ok) {
        const userData = await response.json();
        setUserBalance(userData.stars_balance || 0);
      }
    } catch (error) {
      console.error('Error loading user balance:', error);
    }
  };

  const handleBalanceUpdate = (newBalance: number) => {
    setUserBalance(newBalance);
  };

  const handlePaymentSuccess = (amount: number, method: string) => {
    setUserBalance(prev => prev + amount);
    setShowPaymentModal(false);
  };

  const goBack = () => {
    window.history.back();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-white border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="sticky top-0 z-10 backdrop-blur-md bg-black/20 border-b border-white/10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={goBack}
                className="text-white hover:bg-white/10"
              >
                <ArrowLeft className="w-4 h-4" />
              </Button>
              
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                  <Trophy className="w-4 h-4 text-white" />
                </div>
                <h1 className="text-xl font-bold text-white">NFT Коллекция</h1>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Баланс звезд */}
              <div className="flex items-center gap-2 bg-black/30 px-3 py-2 rounded-lg">
                <Star className="w-4 h-4 text-yellow-400" />
                <span className="text-white font-semibold">{userBalance}</span>
              </div>

              {/* Кнопка пополнения */}
              <Button
                size="sm"
                onClick={() => setShowPaymentModal(true)}
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
              >
                <Package className="w-4 h-4 mr-2" />
                Купить звезды
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Контент */}
      <div className="container mx-auto px-4 py-6">
        {/* Приветственная секция */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-500/20 to-pink-500/20 px-4 py-2 rounded-full mb-4">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-purple-300 text-sm font-medium">
              Добро пожаловать в мир NFT
            </span>
          </div>
          
          <h2 className="text-2xl font-bold text-white mb-2">
            Собирайте уникальные NFT
          </h2>
          <p className="text-gray-300 max-w-md mx-auto">
            Открывайте кейсы, собирайте редкие предметы и создавайте свою уникальную коллекцию
          </p>
        </motion.div>

        {/* Компонент NFT коллекции */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          {user?.id && (
            <NFTCollection
              userId={user.id.toString()}
              userBalance={userBalance}
              onBalanceUpdate={handleBalanceUpdate}
            />
          )}
        </motion.div>
      </div>

      {/* Модальное окно оплаты */}
      <PaymentModal
        isOpen={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        onSuccess={handlePaymentSuccess}
        userBalance={userBalance}
      />

      {/* Фоновые эффекты */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-pink-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
      </div>
    </div>
  );
};

export default NFTPage;
