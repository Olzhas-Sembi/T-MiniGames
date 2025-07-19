import { FaPlay, FaStar, FaTrophy } from 'react-icons/fa';

interface Game {
  id: string;
  name: string;
  description: string;
  icon: string;
  difficulty: 'Легко' | 'Средне' | 'Сложно';
  color: string;
}

interface GameSelectionProps {
  games: Game[];
  onGameSelect: (gameId: string) => void;
  userScore: number;
}

const GameSelection: React.FC<GameSelectionProps> = ({ games, onGameSelect, userScore }) => {
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Легко':
        return 'bg-green-500 text-white';
      case 'Средне':
        return 'bg-yellow-500 text-white';
      case 'Сложно':
        return 'bg-red-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Приветствие */}
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold text-white mb-4 drop-shadow-lg">
          🎮 Выберите игру
        </h2>
        <p className="text-white/80 text-lg max-w-2xl mx-auto">
          Коллекция классических мини-игр с современным дизайном. Играйте, получайте удовольствие и устанавливайте рекорды!
        </p>
      </div>

      {/* Статистика пользователя */}
      <div className="glass-effect rounded-3xl p-6 mb-8 border border-white/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-gradient-to-r from-yellow-400 to-orange-500 p-4 rounded-2xl">
              <FaTrophy className="text-white text-2xl" />
            </div>
            <div>
              <h3 className="text-white text-xl font-bold">Ваш счет</h3>
              <p className="text-white/70">Общий рекорд во всех играх</p>
            </div>
          </div>
          <div className="text-3xl font-bold text-white">
            {userScore.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Сетка игр */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {games.map((game) => (
          <div
            key={game.id}
            className="glass-effect rounded-3xl p-6 border border-white/20 card-hover group cursor-pointer"
            onClick={() => onGameSelect(game.id)}
          >
            {/* Иконка и сложность */}
            <div className="flex items-start justify-between mb-4">
              <div className="text-4xl">{game.icon}</div>
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${getDifficultyColor(game.difficulty)}`}>
                {game.difficulty}
              </span>
            </div>

            {/* Название и описание */}
            <h3 className="text-white text-xl font-bold mb-2 group-hover:text-blue-200 transition-colors">
              {game.name}
            </h3>
            <p className="text-white/70 text-sm mb-6">
              {game.description}
            </p>

            {/* Кнопка играть */}
            <button
              className={`w-full bg-gradient-to-r ${game.color} text-white py-3 px-6 rounded-2xl font-bold flex items-center justify-center gap-3 hover:scale-105 transition-all duration-300 shadow-lg group-hover:shadow-xl`}
            >
              <FaPlay className="text-sm" />
              Играть
            </button>

            {/* Звезды рейтинга */}
            <div className="flex items-center justify-center mt-4 gap-1">
              {[...Array(5)].map((_, i) => (
                <FaStar key={i} className="text-yellow-400 text-sm" />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Дополнительная информация */}
      <div className="text-center mt-12">
        <div className="glass-effect rounded-2xl p-6 border border-white/20">
          <h4 className="text-white font-bold mb-2">💡 Подсказка</h4>
          <p className="text-white/70 text-sm">
            Все игры оптимизированы для мобильных устройств и работают без подключения к интернету
          </p>
        </div>
      </div>
    </div>
  );
};

export default GameSelection;
