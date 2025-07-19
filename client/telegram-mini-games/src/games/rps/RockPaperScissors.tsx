import { useState, useEffect } from 'react';
import { FaArrowLeft, FaPlay, FaCrown, FaCoins, FaHandRock, FaHandPaper, FaHandScissors } from 'react-icons/fa';

interface RPSGameProps {
  onBack: () => void;
  playerName: string;
}

interface Player {
  id: number;
  name: string;
  choice: 'rock' | 'paper' | 'scissors' | null;
  isWinner: boolean;
  hasChosen: boolean;
}

type Choice = 'rock' | 'paper' | 'scissors';

const RockPaperScissors: React.FC<RPSGameProps> = ({ onBack, playerName }) => {
  const [players, setPlayers] = useState<Player[]>([
    { id: 1, name: playerName, choice: null, isWinner: false, hasChosen: false },
    { id: 2, name: 'Игрок 2', choice: null, isWinner: false, hasChosen: false },
    { id: 3, name: 'Игрок 3', choice: null, isWinner: false, hasChosen: false },
    { id: 4, name: 'Игрок 4', choice: null, isWinner: false, hasChosen: false },
  ]);
  
  const [gameState, setGameState] = useState<'waiting' | 'choosing' | 'results' | 'draw'>('waiting');
  const [playerChoice, setPlayerChoice] = useState<Choice | null>(null);
  const [timer, setTimer] = useState(15);
  const [prizePool] = useState(100);

  // Таймер обратного отсчёта
  useEffect(() => {
    let interval: number;
    
    if (gameState === 'choosing' && timer > 0) {
      interval = setInterval(() => {
        setTimer(prev => {
          if (prev <= 1) {
            // Время вышло, завершаем выбор
            if (!playerChoice) {
              // Если игрок не выбрал, выбираем случайно
              const randomChoice: Choice = ['rock', 'paper', 'scissors'][Math.floor(Math.random() * 3)] as Choice;
              setPlayerChoice(randomChoice);
            }
            finishChoosing();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => clearInterval(interval);
  }, [gameState, timer, playerChoice]);

  // Генерация выборов для ботов
  const generateBotChoices = (): Choice[] => {
    const choices: Choice[] = ['rock', 'paper', 'scissors'];
    return [
      choices[Math.floor(Math.random() * 3)],
      choices[Math.floor(Math.random() * 3)],
      choices[Math.floor(Math.random() * 3)]
    ];
  };

  // Определение победителей
  const determineWinners = (allChoices: { [key: number]: Choice }) => {
    const choiceValues = Object.values(allChoices);
    const uniqueChoices = [...new Set(choiceValues)];

    // Если все выбрали одинаково - ничья
    if (uniqueChoices.length === 1) {
      return 'all-draw';
    }

    // Если есть все три варианта - кольцевая ничья
    if (uniqueChoices.length === 3) {
      return 'ring-draw';
    }

    // Определяем победителей по правилам
    const [choice1, choice2] = uniqueChoices;
    let winningChoice: Choice;

    if ((choice1 === 'rock' && choice2 === 'scissors') || 
        (choice1 === 'scissors' && choice2 === 'rock')) {
      winningChoice = 'rock';
    } else if ((choice1 === 'paper' && choice2 === 'rock') || 
               (choice1 === 'rock' && choice2 === 'paper')) {
      winningChoice = 'paper';
    } else {
      winningChoice = 'scissors';
    }

    return winningChoice;
  };

  // Запуск игры
  const startGame = () => {
    setGameState('choosing');
    setTimer(15);
    setPlayerChoice(null);
    setPlayers(prev => prev.map(p => ({
      ...p,
      choice: null,
      isWinner: false,
      hasChosen: false
    })));
  };

  // Выбор игрока
  const makeChoice = (choice: Choice) => {
    setPlayerChoice(choice);
    setPlayers(prev => prev.map(p => 
      p.id === 1 ? { ...p, choice, hasChosen: true } : p
    ));
  };

  // Завершение выбора
  const finishChoosing = () => {
    const botChoices = generateBotChoices();
    const finalPlayerChoice = playerChoice || (['rock', 'paper', 'scissors'][Math.floor(Math.random() * 3)] as Choice);
    
    const allChoices = {
      1: finalPlayerChoice,
      2: botChoices[0],
      3: botChoices[1],
      4: botChoices[2]
    };

    const updatedPlayers = players.map(player => ({
      ...player,
      choice: allChoices[player.id as keyof typeof allChoices],
      hasChosen: true
    }));

    const result = determineWinners(allChoices);

    if (result === 'all-draw' || result === 'ring-draw') {
      setPlayers(updatedPlayers);
      setGameState('draw');
    } else {
      const winnersUpdated = updatedPlayers.map(player => ({
        ...player,
        isWinner: player.choice === result
      }));
      setPlayers(winnersUpdated);
      setGameState('results');
    }
  };

  // Новая игра
  const newGame = () => {
    setGameState('waiting');
    setPlayerChoice(null);
    setTimer(15);
  };

  // Иконки для выборов
  const getChoiceIcon = (choice: Choice | null, size = 'text-4xl') => {
    switch (choice) {
      case 'rock':
        return <FaHandRock className={`${size} text-gray-600`} />;
      case 'paper':
        return <FaHandPaper className={`${size} text-blue-600`} />;
      case 'scissors':
        return <FaHandScissors className={`${size} text-red-600`} />;
      default:
        return <div className={`${size} text-gray-400`}>❓</div>;
    }
  };

  const getChoiceName = (choice: Choice | null) => {
    switch (choice) {
      case 'rock': return 'Камень';
      case 'paper': return 'Бумага';
      case 'scissors': return 'Ножницы';
      default: return '???';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-blue-600 to-purple-500 relative overflow-hidden">
      {/* Декоративные элементы */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-white/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '1.5s' }}></div>
      </div>

      {/* Контент */}
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Заголовок */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={onBack}
            className="glass-effect p-4 rounded-2xl border border-white/20 hover:bg-white/20 transition-colors"
          >
            <FaArrowLeft className="text-white text-xl" />
          </button>
          
          <div className="text-center">
            <h1 className="text-4xl font-bold text-white mb-2 drop-shadow-2xl">
              Камень-Ножницы-Бумага
            </h1>
            <div className="flex items-center justify-center gap-2 text-white/90">
              <FaCoins className="text-yellow-300" />
              <span className="text-lg font-semibold">Банк: {prizePool} ⭐</span>
            </div>
          </div>
          
          <div className="w-16"></div>
        </div>

        {/* Состояние игры */}
        {gameState === 'waiting' && (
          <div className="text-center mb-12">
            <div className="glass-effect rounded-3xl p-8 max-w-md mx-auto border border-white/20">
              <div className="flex justify-center gap-4 mb-6">
                <FaHandRock className="text-6xl text-gray-300" />
                <FaHandPaper className="text-6xl text-blue-300" />
                <FaHandScissors className="text-6xl text-red-300" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">
                Готовы к битве?
              </h2>
              <p className="text-white/80 mb-8">
                Сделайте свой выбор и победите соперников!
              </p>
              <button
                onClick={startGame}
                className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-8 py-4 rounded-2xl font-bold text-lg hover:from-yellow-500 hover:to-orange-600 transition-all duration-300 transform hover:scale-105 shadow-xl flex items-center gap-3 mx-auto"
              >
                <FaPlay />
                Начать игру!
              </button>
            </div>
          </div>
        )}

        {/* Выбор игрока */}
        {gameState === 'choosing' && (
          <div className="text-center mb-12">
            <div className="glass-effect rounded-3xl p-8 max-w-2xl mx-auto border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-4">
                Сделайте свой выбор!
              </h2>
              <div className="text-xl text-white/80 mb-6">
                Осталось времени: {timer}с
              </div>
              
              <div className="flex justify-center gap-6 mb-6">
                {(['rock', 'paper', 'scissors'] as Choice[]).map((choice) => (
                  <button
                    key={choice}
                    onClick={() => makeChoice(choice)}
                    className={`glass-effect p-6 rounded-2xl border transition-all duration-300 hover:scale-110 ${
                      playerChoice === choice 
                        ? 'border-yellow-400 bg-yellow-400/20' 
                        : 'border-white/20 hover:border-white/40'
                    }`}
                  >
                    {getChoiceIcon(choice, 'text-5xl')}
                    <div className="text-white font-semibold mt-2">
                      {getChoiceName(choice)}
                    </div>
                  </button>
                ))}
              </div>

              {playerChoice && (
                <div className="text-green-400 font-semibold">
                  Выбор сделан: {getChoiceName(playerChoice)}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Сетка игроков */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {players.map((player) => (
            <div
              key={player.id}
              className={`glass-effect rounded-3xl p-6 border transition-all duration-300 ${
                player.isWinner 
                  ? 'border-yellow-400 bg-gradient-to-br from-yellow-400/20 to-orange-400/20' 
                  : 'border-white/20'
              }`}
            >
              {/* Имя игрока */}
              <div className="text-center mb-4">
                <div className="flex items-center justify-center gap-2 mb-2">
                  {player.isWinner && <FaCrown className="text-yellow-400" />}
                  <h3 className="text-lg font-bold text-white">{player.name}</h3>
                </div>
                {player.isWinner && (
                  <div className="text-yellow-400 text-sm font-semibold">Победитель! 🎉</div>
                )}
              </div>

              {/* Выбор */}
              <div className="text-center mb-4">
                <div className="flex justify-center mb-3">
                  {gameState === 'results' || gameState === 'draw' || player.id === 1 ? 
                    getChoiceIcon(player.choice) : 
                    <div className="text-4xl text-gray-400">❓</div>
                  }
                </div>
                <div className="text-white font-semibold">
                  {gameState === 'results' || gameState === 'draw' || player.id === 1 ? 
                    getChoiceName(player.choice) : 
                    player.hasChosen ? 'Выбор сделан' : 'Выбирает...'
                  }
                </div>
              </div>

              {/* Статус */}
              <div className="text-center">
                {gameState === 'choosing' && (
                  <div className={`text-sm ${player.hasChosen ? 'text-green-400' : 'text-yellow-400'}`}>
                    {player.hasChosen ? '✓ Готов' : '⏰ Выбирает'}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Результаты игры */}
        {(gameState === 'results' || gameState === 'draw') && (
          <div className="text-center mt-12">
            <div className="glass-effect rounded-3xl p-8 max-w-2xl mx-auto border border-white/20">
              <h2 className="text-3xl font-bold text-white mb-6">
                {gameState === 'draw' ? 'Ничья!' : 'Результаты игры'}
              </h2>
              
              {gameState === 'draw' ? (
                <div className="text-center">
                  <div className="text-xl text-white/90 mb-4">
                    🤝 Все ставки возвращаются игрокам
                  </div>
                  <div className="text-lg text-gray-300 mb-8">
                    Попробуйте ещё раз!
                  </div>
                </div>
              ) : (
                (() => {
                  const winners = players.filter(p => p.isWinner);
                  const prizePerWinner = Math.floor(prizePool / winners.length);
                  
                  return (
                    <div className="text-center">
                      <div className="text-xl text-white/90 mb-4">
                        {winners.length === 1 
                          ? `🎉 Поздравляем ${winners[0].name}!`
                          : `🎉 Победители: ${winners.map(w => w.name).join(', ')}!`
                        }
                      </div>
                      <div className="text-lg text-yellow-400 font-semibold mb-8">
                        Каждый победитель получает: {prizePerWinner} ⭐
                      </div>
                    </div>
                  );
                })()
              )}
              
              <button
                onClick={newGame}
                className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-2xl font-bold text-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-xl"
              >
                Играть ещё
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RockPaperScissors;
