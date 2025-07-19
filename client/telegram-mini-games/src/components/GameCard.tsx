import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FaPlay, FaUsers } from 'react-icons/fa';

interface GameCardProps {
  game: {
    id: string;
    name: string;
    description: string;
    icon: string;
    color: string;
    difficulty: string;
    players?: string;
  };
  onClick: () => void;
  index: number;
}

export const GameCard: React.FC<GameCardProps> = ({ game, onClick, index }) => {
  const [isHovered, setIsHovered] = useState(false);

  const getDifficultyConfig = (difficulty: string) => {
    switch (difficulty) {
      case 'Легко':
        return { 
          bg: 'bg-green-500/20', 
          text: 'text-green-400', 
          icon: '😊',
          glow: 'shadow-green-500/30'
        };
      case 'Средне':
        return { 
          bg: 'bg-yellow-500/20', 
          text: 'text-yellow-400', 
          icon: '😐',
          glow: 'shadow-yellow-500/30'
        };
      case 'Сложно':
        return { 
          bg: 'bg-red-500/20', 
          text: 'text-red-400', 
          icon: '😓',
          glow: 'shadow-red-500/30'
        };
      default:
        return { 
          bg: 'bg-blue-500/20', 
          text: 'text-blue-400', 
          icon: '🎮',
          glow: 'shadow-blue-500/30'
        };
    }
  };

  const difficultyConfig = getDifficultyConfig(game.difficulty);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ 
        delay: index * 0.1, 
        type: 'spring', 
        stiffness: 100,
        damping: 15
      }}
      whileHover={{ 
        y: -8,
        transition: { duration: 0.3, ease: 'easeOut' }
      }}
      whileTap={{ scale: 0.95 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={onClick}
      className="relative glass-effect rounded-3xl p-6 border border-white/20 overflow-hidden cursor-pointer group"
    >
      {/* Бейдж сложности */}
      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: index * 0.1 + 0.2 }}
        className={`absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-bold ${difficultyConfig.bg} ${difficultyConfig.text} flex items-center gap-1`}
      >
        <span>{difficultyConfig.icon}</span>
        {game.difficulty}
      </motion.div>
      
      {/* Количество игроков */}
      {game.players && (
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: index * 0.1 + 0.3 }}
          className="absolute top-4 left-4 px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-400 flex items-center gap-1"
        >
          <FaUsers className="text-xs" />
          {game.players}
        </motion.div>
      )}
      
      {/* Иконка игры с анимацией */}
      <motion.div
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ 
          delay: index * 0.1 + 0.1,
          type: 'spring',
          stiffness: 200,
          damping: 20
        }}
        whileHover={{ 
          scale: 1.1,
          rotate: [0, 5, -5, 0],
          transition: { duration: 0.5, ease: 'easeInOut' }
        }}
        className={`bg-gradient-to-br ${game.color} w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl relative overflow-hidden`}
      >
        {/* Эффект блеска */}
        <motion.div
          initial={{ x: '-100%', opacity: 0 }}
          animate={isHovered ? { x: '100%', opacity: [0, 1, 0] } : {}}
          transition={{ duration: 0.6 }}
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent skew-x-12"
        />
        <span className="text-3xl relative z-10">{game.icon}</span>
      </motion.div>
      
      {/* Контент */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 + 0.4 }}
      >
        <h3 className="text-xl font-bold text-white mb-2 text-center group-hover:text-blue-300 transition-colors">
          {game.name}
        </h3>
        <p className="text-white/70 text-sm mb-6 text-center leading-relaxed">
          {game.description}
        </p>
      </motion.div>
      
      {/* Кнопка с анимацией */}
      <motion.button
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: index * 0.1 + 0.5 }}
        whileTap={{ scale: 0.95 }}
        whileHover={{ scale: 1.02 }}
        className={`w-full bg-gradient-to-r ${game.color} text-white py-3 px-6 rounded-2xl font-bold flex items-center justify-center gap-3 relative overflow-hidden group/button`}
      >
        {/* Эффект свечения кнопки */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isHovered ? { opacity: 1 } : { opacity: 0 }}
          className="absolute inset-0 bg-white/10"
        />
        
        <motion.div
          whileHover={{ x: 2 }}
          transition={{ type: 'spring', stiffness: 300 }}
        >
          <FaPlay className="text-sm" />
        </motion.div>
        <span className="relative z-10">Играть</span>
        
        {/* Эффект волны */}
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          whileTap={{ scale: 2, opacity: [0, 0.3, 0] }}
          transition={{ duration: 0.3 }}
          className="absolute inset-0 rounded-2xl bg-white"
        />
      </motion.button>
      
      {/* Эффект свечения при наведении */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={isHovered ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.8 }}
        transition={{ duration: 0.3 }}
        className={`absolute inset-0 rounded-3xl pointer-events-none -z-10 blur-xl ${difficultyConfig.glow}`}
        style={{
          background: `linear-gradient(135deg, ${game.color.includes('blue') ? '#3b82f6' : 
                      game.color.includes('green') ? '#10b981' : 
                      game.color.includes('purple') ? '#8b5cf6' : 
                      game.color.includes('orange') ? '#f59e0b' : '#ef4444'}33, transparent)`
        }}
      />

      {/* Частицы при наведении */}
      {isHovered && (
        <>
          {[...Array(5)].map((_, i) => (
            <motion.div
              key={i}
              initial={{ 
                scale: 0, 
                x: Math.random() * 200 - 100, 
                y: Math.random() * 200 - 100,
                opacity: 0
              }}
              animate={{ 
                scale: [0, 1, 0], 
                y: -50,
                opacity: [0, 1, 0]
              }}
              transition={{ 
                duration: 1.5, 
                delay: i * 0.1,
                repeat: Infinity,
                repeatDelay: 2
              }}
              className="absolute w-1 h-1 bg-white rounded-full pointer-events-none"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`
              }}
            />
          ))}
        </>
      )}
    </motion.div>
  );
};
