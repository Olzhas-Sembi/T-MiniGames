import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaDice, FaArrowLeft, FaCrown, FaCoins, FaUsers, FaClock, FaTrophy } from 'react-icons/fa';

interface DiceGameProps {
  onBack: () => void;
  playerName: string;
  playerId: string;
  websocket: WebSocket | null;
  roomData?: any;
}

interface DiceResult {
  player_id: string;
  player_name: string;
  dice1: number;
  dice2: number;
  total: number;
}

interface GameState {
  room_id: string;
  round_number: number;
  player_actions: Record<string, boolean>;
  results: Record<string, DiceResult>;
  winners: string[];
  game_finished: boolean;
  all_players_rolled: boolean;
  prize_pool: number;
  seed?: string;
  nonce?: string;
}

interface Player {
  id: string;
  name: string;
  stars: number;
  isReady: boolean;
}

const DiceGame: React.FC<DiceGameProps> = ({ 
  onBack, 
  playerId, 
  websocket,
  roomData 
}) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [gamePhase, setGamePhase] = useState<'waiting' | 'rolling' | 'results' | 'reroll'>('waiting');
  const [hasRolled, setHasRolled] = useState(false);
  const [players, setPlayers] = useState<Player[]>([]);
  const [isRolling, setIsRolling] = useState(false);
  const [rollAnimation, setRollAnimation] = useState<{ dice1: number; dice2: number } | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [countdown, setCountdown] = useState<number>(0);

  // Эффект обратного отсчета
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (countdown > 0) {
      interval = setInterval(() => {
        setCountdown(prev => prev - 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [countdown]);

  // Обработка WebSocket сообщений согласно ТЗ
  useEffect(() => {
    if (!websocket) return;

    const handleMessage = (event: MessageEvent) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'game_start':
          setGamePhase('rolling');
          setCountdown(30); // 30 секунд на бросок
          setPlayers(message.players || []);
          setGameState(message.game_state);
          break;
          
        case 'dice_roll_result':
          setGameState(message.game_state);
          if (message.all_players_rolled) {
            setGamePhase('results');
            setCountdown(0);
          }
          break;
          
        case 'game_results':
          setGameState(message.game_state);
          setGamePhase('results');
          // Публикуем seed и nonce для проверки честности
          if (message.seed && message.nonce) {
            console.log('Cryptographic proof:', { seed: message.seed, nonce: message.nonce });
          }
          break;
          
        case 'tie_detected':
          setGamePhase('reroll');
          setCountdown(10); // 10 секунд до автоматического переброса
          break;
          
        case 'error':
          setErrorMessage(message.error);
          break;
      }
    };

    websocket.addEventListener('message', handleMessage);
    return () => websocket.removeEventListener('message', handleMessage);
  }, [websocket]);

  // Функция броска кубиков согласно ТЗ
  const rollDice = async () => {
    if (!websocket || hasRolled || gamePhase !== 'rolling') return;
    
    setIsRolling(true);
    setHasRolled(true);
    
    // Анимация прокрутки кубиков
    const animationDuration = 2000; // 2 секунды анимации
    const interval = setInterval(() => {
      setRollAnimation({
        dice1: Math.floor(Math.random() * 6) + 1,
        dice2: Math.floor(Math.random() * 6) + 1
      });
    }, 100);
    
    // Отправляем действие на сервер
    websocket.send(JSON.stringify({
      action: 'dice_action',
      dice_action: 'roll',
      player_id: playerId,
      room_id: roomData?.room_id
    }));
    
    // Останавливаем анимацию
    setTimeout(() => {
      clearInterval(interval);
      setIsRolling(false);
      setRollAnimation(null);
    }, animationDuration);
  };

  // Рендер кубика с улучшенным дизайном
  const renderDice = (value: number, isAnimating: boolean = false) => (
    <motion.div
      className={`w-24 h-24 bg-gradient-to-br from-white to-gray-100 rounded-2xl shadow-2xl flex items-center justify-center text-4xl font-bold border-2 border-gray-200 ${
        isAnimating ? 'animate-bounce' : ''
      }`}
      animate={isAnimating ? { 
        rotateY: [0, 360],
        scale: [1, 1.1, 1],
        rotateZ: [0, 180, 360] 
      } : {}}
      transition={{ duration: 0.15, repeat: isAnimating ? Infinity : 0 }}
      whileHover={{ scale: 1.05 }}
      style={{
        background: isAnimating 
          ? 'linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #ffeaa7)'
          : 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 50%, #e9ecef 100%)',
        backgroundSize: isAnimating ? '400% 400%' : 'auto',
        animation: isAnimating ? 'gradientShift 0.5s ease infinite' : 'none'
      }}
    >
      <span className={isAnimating ? 'text-white' : 'text-gray-800'}>
        {getDiceSymbol(value)}
      </span>
    </motion.div>
  );

  const getDiceSymbol = (value: number) => {
    const symbols = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];
    return symbols[value - 1] || '⚀';
  };

  // Рендер результатов игроков с улучшенным дизайном
  const renderPlayerResults = () => {
    if (!gameState?.results) return null;

    const sortedResults = Object.values(gameState.results).sort((a, b) => b.total - a.total);
    
    return (
      <div className="space-y-6">
        {sortedResults.map((result, index) => {
          const isWinner = gameState.winners.includes(result.player_id);
          
          return (
            <motion.div
              key={result.player_id}
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.2, type: "spring", stiffness: 100 }}
              className={`p-6 rounded-3xl border-2 shadow-2xl ${
                isWinner 
                  ? 'bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 border-yellow-300 text-white' 
                  : 'bg-white/20 backdrop-blur-md border-white/30 text-white'
              }`}
              whileHover={{ scale: 1.02 }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {isWinner && (
                    <motion.div
                      animate={{ rotate: [0, 10, -10, 0] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="p-2 bg-yellow-300 rounded-full"
                    >
                      <FaCrown className="text-2xl text-yellow-600" />
                    </motion.div>
                  )}
                  <div>
                    <span className="font-bold text-xl">{result.player_name}</span>
                    {index === 0 && !isWinner && (
                      <div className="text-sm opacity-75">Лидер</div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex gap-3">
                    <motion.div
                      whileHover={{ scale: 1.1, rotateY: 180 }}
                      transition={{ duration: 0.3 }}
                    >
                      {renderDice(result.dice1)}
                    </motion.div>
                    <motion.div
                      whileHover={{ scale: 1.1, rotateY: 180 }}
                      transition={{ duration: 0.3 }}
                    >
                      {renderDice(result.dice2)}
                    </motion.div>
                  </div>
                  <motion.div
                    className={`text-2xl font-bold px-6 py-3 rounded-2xl shadow-lg ${
                      isWinner
                        ? 'bg-white/20 text-white'
                        : 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                    }`}
                    whileHover={{ scale: 1.05 }}
                  >
                    = {result.total}
                  </motion.div>
                </div>
              </div>
              
              {/* Дополнительная информация для победителя */}
              {isWinner && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  transition={{ delay: 0.5 }}
                  className="mt-4 pt-4 border-t border-white/30"
                >
                  <div className="flex items-center justify-center gap-2 text-sm">
                    <FaTrophy className="text-yellow-200" />
                    <span>Победитель раунда!</span>
                  </div>
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 relative overflow-hidden">
      {/* Анимированный фон */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-10 left-10 w-32 h-32 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 right-20 w-48 h-48 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full blur-3xl animate-bounce" style={{animationDuration: '3s'}}></div>
        <div className="absolute bottom-20 left-1/3 w-40 h-40 bg-gradient-to-r from-green-400 to-blue-400 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
      </div>
      
      <div className="relative z-10 p-4">
        <div className="max-w-5xl mx-auto">
          {/* Заголовок с улучшенным дизайном */}
          <div className="flex items-center justify-between mb-8">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onBack}
              className="flex items-center gap-2 px-6 py-3 bg-white/10 backdrop-blur-md text-white rounded-2xl border border-white/20 hover:bg-white/20 transition-all duration-300 shadow-lg"
            >
              <FaArrowLeft />
              Назад к играм
            </motion.button>
            
            <div className="text-center">
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-center gap-4 mb-2"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className="p-3 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-2xl shadow-lg"
                >
                  <FaDice className="text-3xl text-white" />
                </motion.div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-yellow-200 to-white bg-clip-text text-transparent">
                  Игра в кубики
                </h1>
              </motion.div>
              <p className="text-white/70 text-lg">Бросьте кубики и наберите наибольшую сумму!</p>
            </div>
            
            <div className="flex items-center gap-3 px-4 py-2 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20">
              <FaUsers className="text-blue-300" />
              <span className="text-white font-semibold">{players.length}/4</span>
            </div>
          </div>

          {/* Информация о комнате с улучшенным дизайном */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white/10 backdrop-blur-md rounded-3xl p-8 mb-8 border border-white/20 shadow-2xl"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="text-center p-6 bg-gradient-to-br from-yellow-400/20 to-orange-500/20 rounded-2xl border border-yellow-300/30"
              >
                <motion.div
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="inline-block p-4 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-2xl mb-4 shadow-lg"
                >
                  <FaCoins className="text-3xl text-white" />
                </motion.div>
                <div className="text-white/70 text-sm mb-2 font-medium">Призовой фонд</div>
                <div className="text-3xl font-bold bg-gradient-to-r from-yellow-200 to-orange-200 bg-clip-text text-transparent">
                  ⭐ {gameState?.prize_pool || roomData?.bet_amount * players.length || 0}
                </div>
              </motion.div>
              
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="text-center p-6 bg-gradient-to-br from-orange-400/20 to-red-500/20 rounded-2xl border border-orange-300/30"
              >
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="inline-block p-4 bg-gradient-to-r from-orange-400 to-red-500 rounded-2xl mb-4 shadow-lg"
                >
                  <FaTrophy className="text-3xl text-white" />
                </motion.div>
                <div className="text-white/70 text-sm mb-2 font-medium">Раунд</div>
                <div className="text-3xl font-bold bg-gradient-to-r from-orange-200 to-red-200 bg-clip-text text-transparent">
                  #{gameState?.round_number || 1}
                </div>
              </motion.div>
              
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="text-center p-6 bg-gradient-to-br from-blue-400/20 to-cyan-500/20 rounded-2xl border border-blue-300/30"
              >
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                  className="inline-block p-4 bg-gradient-to-r from-blue-400 to-cyan-500 rounded-2xl mb-4 shadow-lg"
                >
                  <FaClock className="text-3xl text-white" />
                </motion.div>
                <div className="text-white/70 text-sm mb-2 font-medium">Время</div>
                <div className="text-3xl font-bold bg-gradient-to-r from-blue-200 to-cyan-200 bg-clip-text text-transparent">
                  {countdown > 0 ? `${countdown}с` : '—'}
                </div>
              </motion.div>
            </div>
          </motion.div>

          {/* Игровое поле с улучшенным дизайном */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-white/15 backdrop-blur-md rounded-3xl p-8 shadow-2xl border border-white/20"
          >
            {gamePhase === 'waiting' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-16"
              >
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="inline-block p-8 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full mb-8 shadow-2xl"
                >
                  <FaUsers className="text-6xl text-white" />
                </motion.div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent mb-6">
                  Ожидание игроков...
                </h2>
                <p className="text-white/70 text-lg">
                  Игра начнется, когда наберется минимум 2 игрока
                </p>
                <div className="mt-8 flex justify-center">
                  <div className="flex space-x-2">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ 
                          duration: 1.5, 
                          repeat: Infinity, 
                          delay: i * 0.2 
                        }}
                        className="w-3 h-3 bg-white rounded-full"
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {gamePhase === 'rolling' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-16"
              >
                <motion.h2
                  initial={{ y: -20 }}
                  animate={{ y: 0 }}
                  className="text-3xl font-bold bg-gradient-to-r from-white to-yellow-200 bg-clip-text text-transparent mb-12"
                >
                  Время бросать кубики!
                </motion.h2>
                
                {/* Кубики игрока с улучшенным дизайном */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 100, delay: 0.2 }}
                  className="flex justify-center gap-8 mb-12"
                >
                  {rollAnimation ? (
                    <>
                      {renderDice(rollAnimation.dice1, true)}
                      {renderDice(rollAnimation.dice2, true)}
                    </>
                  ) : gameState?.results[playerId] ? (
                    <>
                      <motion.div
                        initial={{ rotateY: 180 }}
                        animate={{ rotateY: 0 }}
                        transition={{ duration: 0.6 }}
                      >
                        {renderDice(gameState.results[playerId].dice1)}
                      </motion.div>
                      <motion.div
                        initial={{ rotateY: 180 }}
                        animate={{ rotateY: 0 }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                      >
                        {renderDice(gameState.results[playerId].dice2)}
                      </motion.div>
                    </>
                  ) : (
                    <>
                      {renderDice(1)}
                      {renderDice(1)}
                    </>
                  )}
                </motion.div>
                
                {/* Результат броска */}
                {gameState?.results[playerId] && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                  >
                    <div className="inline-block px-8 py-4 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-2xl shadow-2xl">
                      <span className="text-2xl font-bold text-white">
                        Сумма: {gameState.results[playerId].total}
                      </span>
                    </div>
                  </motion.div>
                )}
                
                {/* Кнопка броска с улучшенным дизайном */}
                {!hasRolled && !isRolling && (
                  <motion.button
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    whileHover={{ 
                      scale: 1.05,
                      boxShadow: "0 20px 40px rgba(0,0,0,0.3)"
                    }}
                    whileTap={{ scale: 0.95 }}
                    onClick={rollDice}
                    className="px-12 py-6 bg-gradient-to-r from-purple-500 via-pink-500 to-red-500 text-white rounded-3xl font-bold text-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 border-2 border-white/20"
                    style={{
                      background: 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)',
                      boxShadow: '0 8px 32px rgba(102, 126, 234, 0.4)'
                    }}
                  >
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      className="inline-block mr-4"
                    >
                      <FaDice />
                    </motion.div>
                    Бросить кубики!
                  </motion.button>
                )}
                
                {(hasRolled || isRolling) && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-white/80 text-lg"
                  >
                    {isRolling ? (
                      <div className="flex items-center justify-center gap-3">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        >
                          <FaDice className="text-2xl" />
                        </motion.div>
                        Бросаем кубики...
                      </div>
                    ) : (
                      'Ожидание других игроков...'
                    )}
                  </motion.div>
                )}
              </motion.div>
            )}

            {gamePhase === 'results' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="py-8"
              >
                <motion.h2
                  initial={{ y: -20 }}
                  animate={{ y: 0 }}
                  className="text-3xl font-bold bg-gradient-to-r from-white to-yellow-200 bg-clip-text text-transparent mb-12 text-center"
                >
                  🎉 Результаты раунда
                </motion.h2>
                
                {renderPlayerResults()}
                
                {gameState?.winners.length && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 100, delay: 0.5 }}
                    className="text-center mt-12 p-8 bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 rounded-3xl shadow-2xl border-2 border-yellow-300/50"
                  >
                    <motion.div
                      animate={{ rotate: [0, 10, -10, 0] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      <FaCrown className="text-5xl text-white mb-4 mx-auto" />
                    </motion.div>
                    <h3 className="text-2xl font-bold text-white mb-4">
                      🎉 Поздравляем победителей!
                    </h3>
                    <div className="flex items-center justify-center gap-2 text-white text-xl">
                      <span>Призовой фонд:</span>
                      <motion.span
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ duration: 1, repeat: Infinity }}
                        className="font-bold"
                      >
                        ⭐ {gameState.prize_pool}
                      </motion.span>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {gamePhase === 'reroll' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-16"
              >
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                  className="inline-block p-6 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full mb-8 shadow-2xl"
                >
                  <FaDice className="text-4xl text-white" />
                </motion.div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent mb-6">
                  Ничья! Переброс через {countdown} секунд
                </h2>
                <p className="text-white/70 text-lg">
                  У игроков одинаковая сумма. Автоматический переброс...
                </p>
              </motion.div>
            )}
          </motion.div>

          {/* Ошибки с улучшенным дизайном */}
          <AnimatePresence>
            {errorMessage && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mt-8 p-6 bg-red-500/20 backdrop-blur-md border border-red-400/50 text-red-100 rounded-2xl shadow-xl"
              >
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">!</span>
                  </div>
                  {errorMessage}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default DiceGame;
