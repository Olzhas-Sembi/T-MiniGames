import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaUsers, FaClock, FaArrowLeft, FaPlay, FaCoins, FaCrown, FaCheckCircle, FaCopy } from 'react-icons/fa';
import type { Room } from '../services/gameAPI';
import { gameWebSocket } from '../services/gameWebSocket';

interface GameLobbyProps {
  room: Room;
  playerId: string;
  playerName: string;
  onBack: () => void;
  onGameStart: (room: Room) => void;
}

export const GameLobbyEnhanced: React.FC<GameLobbyProps> = ({
  room: initialRoom,
  playerId,
  onBack,
  onGameStart
}) => {
  const [room, setRoom] = useState<Room>(initialRoom);
  const [timeLeft, setTimeLeft] = useState(60);
  const [isLoading, setIsLoading] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  useEffect(() => {
    // Подключаемся к WebSocket если еще не подключены
    if (!gameWebSocket.isConnected()) {
      gameWebSocket.connect().catch(console.error);
    }

    // Подписываемся на обновления комнаты
    const handleRoomUpdate = (data: any) => {
      if (data.room_id === room.id) {
        setRoom(data.room);
        
        if (data.type === 'game_started') {
          onGameStart(data.room);
        }
      }
    };

    const handlePlayerJoined = handleRoomUpdate;
    const handlePlayerReady = handleRoomUpdate;
    const handleGameStarted = handleRoomUpdate;
    const handleRoomCancelled = (data: any) => {
      if (data.room_id === room.id) {
        alert('Комната отменена: ' + data.data.message);
        onBack();
      }
    };

    gameWebSocket.on('player_joined', handlePlayerJoined);
    gameWebSocket.on('player_ready', handlePlayerReady);
    gameWebSocket.on('game_started', handleGameStarted);
    gameWebSocket.on('room_cancelled', handleRoomCancelled);

    return () => {
      gameWebSocket.off('player_joined', handlePlayerJoined);
      gameWebSocket.off('player_ready', handlePlayerReady);
      gameWebSocket.off('game_started', handleGameStarted);
      gameWebSocket.off('room_cancelled', handleRoomCancelled);
    };
  }, [room.id, onGameStart, onBack]);

  // Таймер
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleReady = async () => {
    setIsLoading(true);
    try {
      await gameWebSocket.sendReady();
    } catch (error) {
      console.error('Ошибка при подтверждении готовности:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const copyInviteLink = () => {
    const inviteLink = `https://t.me/your_bot?startapp=join_${room.id}`;
    navigator.clipboard.writeText(inviteLink);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  const currentPlayer = room.players?.find(p => p.id === playerId);
  const readyPlayersCount = room.players?.filter(p => p.status === 'ready').length || 0;
  const canStart = readyPlayersCount >= (room.min_players || 2);

  const getGameIcon = (gameType: string) => {
    switch (gameType) {
      case 'dice': return '🎲';
      case 'cards': return '🃏';
      case 'rps': return '✂️';
      default: return '🎮';
    }
  };

  const getGameName = (gameType: string) => {
    switch (gameType) {
      case 'dice': return 'Кубики';
      case 'cards': return 'Карты 21';
      case 'rps': return 'Камень-Ножницы-Бумага';
      default: return 'Игра';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4"
    >
      {/* Заголовок */}
      <motion.div
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="glass-effect rounded-3xl p-6 mb-8 border border-white/20"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={onBack}
              className="glass-effect p-3 rounded-xl hover:bg-white/20 transition-all duration-300 border border-white/20"
            >
              <FaArrowLeft className="text-white text-xl" />
            </motion.button>
            <div className="flex items-center gap-3">
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                className="bg-gradient-to-br from-blue-400 to-blue-600 w-12 h-12 rounded-xl flex items-center justify-center shadow-xl"
              >
                <span className="text-2xl">{getGameIcon(room.game_type)}</span>
              </motion.div>
              <div>
                <h1 className="text-2xl font-bold text-white">{getGameName(room.game_type)}</h1>
                <p className="text-blue-300">Лобби игры</p>
              </div>
            </div>
          </div>
          
          {/* Кнопка поделиться */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={copyInviteLink}
            className="flex items-center gap-2 px-4 py-2 glass-effect rounded-xl border border-white/20 hover:bg-white/10 transition-all duration-300"
          >
            <AnimatePresence mode="wait">
              {linkCopied ? (
                <motion.div
                  key="copied"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="flex items-center gap-2 text-green-400"
                >
                  <FaCheckCircle />
                  <span className="text-sm font-medium">Скопировано!</span>
                </motion.div>
              ) : (
                <motion.div
                  key="copy"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="flex items-center gap-2 text-white"
                >
                  <FaCopy />
                  <span className="text-sm font-medium">Пригласить</span>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Основная информация */}
        <div className="lg:col-span-2 space-y-6">
          {/* Таймер */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="glass-effect rounded-3xl p-8 border border-white/20 text-center"
          >
            <div className="flex items-center justify-center gap-3 mb-4">
              <FaClock className="text-blue-400 text-2xl" />
              <h3 className="text-xl font-bold text-white">Время до автостарта</h3>
            </div>
            
            <motion.div
              key={timeLeft}
              initial={{ scale: 1.2, color: timeLeft <= 10 ? '#ef4444' : '#ffffff' }}
              animate={{ scale: 1, color: timeLeft <= 10 ? '#ef4444' : '#ffffff' }}
              transition={{ type: 'spring', stiffness: 300 }}
              className="text-6xl font-bold mb-4"
            >
              {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
            </motion.div>
            
            {/* Прогресс бар */}
            <div className="w-full bg-white/10 rounded-full h-3 mb-4">
              <motion.div
                initial={{ width: '100%' }}
                animate={{ width: `${(timeLeft / 60) * 100}%` }}
                transition={{ duration: 1 }}
                className={`h-full rounded-full ${
                  timeLeft <= 10 ? 'bg-red-500' : timeLeft <= 30 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
              />
            </div>
            
            <p className="text-white/60">
              {timeLeft <= 10 ? '⚠️ Игра скоро начнется!' : 'Ожидаем игроков...'}
            </p>
          </motion.div>

          {/* Информация о комнате */}
          <motion.div
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="glass-effect rounded-3xl p-6 border border-white/20"
          >
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <FaCoins className="text-yellow-400" />
              Информация об игре
            </h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-white/60 text-sm">Ставка</p>
                <p className="text-white text-lg font-bold">{room.bet_amount} ⭐</p>
              </div>
              <div className="text-center">
                <p className="text-white/60 text-sm">Банк</p>
                <motion.p
                  key={room.pot}
                  initial={{ scale: 1.2, color: '#fbbf24' }}
                  animate={{ scale: 1, color: '#ffffff' }}
                  className="text-white text-lg font-bold"
                >
                  {room.pot} ⭐
                </motion.p>
              </div>
              <div className="text-center">
                <p className="text-white/60 text-sm">Игроков</p>
                <p className="text-white text-lg font-bold">
                  {room.players?.length || 0}/{room.max_players || 4}
                </p>
              </div>
              <div className="text-center">
                <p className="text-white/60 text-sm">Готовы</p>
                <motion.p
                  key={readyPlayersCount}
                  initial={{ scale: 1.2, color: '#10b981' }}
                  animate={{ scale: 1, color: '#ffffff' }}
                  className="text-white text-lg font-bold"
                >
                  {readyPlayersCount}/{room.players?.length || 0}
                </motion.p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Панель игроков */}
        <div className="space-y-6">
          {/* Список игроков */}
          <motion.div
            initial={{ x: 50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="glass-effect rounded-3xl p-6 border border-white/20"
          >
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <FaUsers className="text-blue-400" />
              Игроки в лобби
            </h3>
            
            <div className="space-y-3">
              <AnimatePresence>
                {room.players?.map((player, index) => (
                  <motion.div
                    key={player.id}
                    initial={{ opacity: 0, x: 20, scale: 0.9 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    exit={{ opacity: 0, x: -20, scale: 0.9 }}
                    transition={{ delay: index * 0.1 }}
                    className={`flex items-center justify-between p-4 rounded-2xl border transition-all duration-300 ${
                      player.status === 'ready'
                        ? 'bg-green-500/20 border-green-500/30'
                        : 'bg-white/5 border-white/10 hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {player.is_creator && (
                        <motion.div
                          initial={{ rotate: -10 }}
                          animate={{ rotate: 0 }}
                          className="text-yellow-400"
                        >
                          <FaCrown />
                        </motion.div>
                      )}
                      <div>
                        <p className="text-white font-medium">{player.username}</p>
                        <p className="text-white/60 text-sm">
                          {player.balance} ⭐
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {player.status === 'ready' ? (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="flex items-center gap-1 text-green-400 text-sm font-medium"
                        >
                          <FaCheckCircle />
                          Готов
                        </motion.div>
                      ) : (
                        <span className="text-white/60 text-sm">Ожидание...</span>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {/* Пустые слоты */}
              {Array.from({ length: (room.max_players || 4) - (room.players?.length || 0) }).map((_, index) => (
                <motion.div
                  key={`empty-${index}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: (room.players?.length || 0) * 0.1 + index * 0.1 }}
                  className="flex items-center justify-center p-4 rounded-2xl border-2 border-dashed border-white/20 text-white/40"
                >
                  <FaUsers className="mr-2" />
                  Ожидание игрока...
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Кнопка готовности */}
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="glass-effect rounded-3xl p-6 border border-white/20"
          >
            {currentPlayer?.status === 'ready' ? (
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className="text-center"
              >
                <div className="flex items-center justify-center gap-2 text-green-400 text-xl mb-3">
                  <FaCheckCircle />
                  <span className="font-bold">Вы готовы!</span>
                </div>
                <p className="text-white/60">
                  {canStart 
                    ? 'Игра начнется, когда все будут готовы' 
                    : `Нужно еще ${(room.min_players || 2) - readyPlayersCount} игроков`
                  }
                </p>
              </motion.div>
            ) : (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={isLoading || (currentPlayer?.balance || 0) < room.bet_amount}
                onClick={handleReady}
                className={`w-full py-4 px-6 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 transition-all duration-300 ${
                  (currentPlayer?.balance || 0) < room.bet_amount
                    ? 'bg-red-500/20 text-red-400 border border-red-500/30 cursor-not-allowed'
                    : 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:from-green-600 hover:to-emerald-700 shadow-lg'
                }`}
              >
                {isLoading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-6 h-6 border-2 border-white border-t-transparent rounded-full"
                  />
                ) : (
                  <>
                    <FaPlay />
                    {(currentPlayer?.balance || 0) < room.bet_amount ? 'Недостаточно звёзд' : 'Готов к игре!'}
                  </>
                )}
              </motion.button>
            )}
          </motion.div>
        </div>
      </div>

      {/* Статус игры */}
      <AnimatePresence>
        {canStart && readyPlayersCount === room.players?.length && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-8 left-1/2 transform -translate-x-1/2 glass-effect rounded-2xl p-4 border border-green-500/30 bg-green-500/10"
          >
            <div className="flex items-center gap-3 text-green-400">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                <FaPlay />
              </motion.div>
              <span className="font-bold">Все готовы! Игра начинается...</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
