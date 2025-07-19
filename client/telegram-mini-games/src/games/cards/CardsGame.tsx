import { useState } from 'react';
import { FaArrowLeft, FaPlay, FaCrown, FaCoins, FaPlus, FaStop } from 'react-icons/fa';

interface CardsGameProps {
  onBack: () => void;
  playerName: string;
}

interface Card {
  suit: string;
  value: string;
  points: number;
}

interface Player {
  id: number;
  name: string;
  cards: Card[];
  score: number;
  isActive: boolean;
  isFinished: boolean;
  isBusted: boolean;
  isWinner: boolean;
}

const CardsGame: React.FC<CardsGameProps> = ({ onBack, playerName }) => {
  const [players, setPlayers] = useState<Player[]>([
    { id: 1, name: playerName, cards: [], score: 0, isActive: false, isFinished: false, isBusted: false, isWinner: false },
    { id: 2, name: 'Игрок 2', cards: [], score: 0, isActive: false, isFinished: false, isBusted: false, isWinner: false },
    { id: 3, name: 'Игрок 3', cards: [], score: 0, isActive: false, isFinished: false, isBusted: false, isWinner: false },
    { id: 4, name: 'Игрок 4', cards: [], score: 0, isActive: false, isFinished: false, isBusted: false, isWinner: false },
  ]);
  
  const [gameState, setGameState] = useState<'waiting' | 'playing' | 'results'>('waiting');
  const [currentPlayerIndex, setCurrentPlayerIndex] = useState(0);
  const [prizePool] = useState(100);
  const [timer, setTimer] = useState(15);

  // Колода карт
  const createDeck = (): Card[] => {
    const suits = ['♠', '♥', '♦', '♣'];
    const values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
    const deck: Card[] = [];

    suits.forEach(suit => {
      values.forEach(value => {
        let points = parseInt(value);
        if (value === 'J' || value === 'Q' || value === 'K') points = 10;
        if (value === 'A') points = 11; // Туз всегда 11 для простоты
        
        deck.push({ suit, value, points });
      });
    });

    return deck.sort(() => Math.random() - 0.5); // Перемешиваем
  };

  // Раздача начальных карт
  const dealInitialCards = () => {
    const deck = createDeck();
    let cardIndex = 0;

    const updatedPlayers = players.map(player => {
      const card1 = deck[cardIndex++];
      const card2 = deck[cardIndex++];
      const cards = [card1, card2];
      const score = calculateScore(cards);

      return {
        ...player,
        cards,
        score,
        isActive: false,
        isFinished: false,
        isBusted: false,
        isWinner: false
      };
    });

    setPlayers(updatedPlayers);
    setCurrentPlayerIndex(0);
    setGameState('playing');
    setTimer(15);
  };

  // Подсчёт очков с учётом тузов
  const calculateScore = (cards: Card[]): number => {
    let score = 0;
    let aces = 0;

    cards.forEach(card => {
      if (card.value === 'A') {
        aces++;
        score += 11;
      } else {
        score += card.points;
      }
    });

    // Корректируем тузы если перебор
    while (score > 21 && aces > 0) {
      score -= 10;
      aces--;
    }

    return score;
  };

  // Взять карту
  const hitCard = () => {
    const deck = createDeck();
    const newCard = deck[Math.floor(Math.random() * deck.length)];
    
    setPlayers(prev => prev.map((player, index) => {
      if (index === currentPlayerIndex) {
        const newCards = [...player.cards, newCard];
        const newScore = calculateScore(newCards);
        const isBusted = newScore > 21;
        
        return {
          ...player,
          cards: newCards,
          score: newScore,
          isBusted,
          isFinished: isBusted
        };
      }
      return player;
    }));

    // Если перебор, переходим к следующему игроку
    const currentPlayer = players[currentPlayerIndex];
    const newScore = calculateScore([...currentPlayer.cards, newCard]);
    if (newScore > 21) {
      nextPlayer();
    }
  };

  // Стоп (остановиться)
  const stand = () => {
    setPlayers(prev => prev.map((player, index) => {
      if (index === currentPlayerIndex) {
        return { ...player, isFinished: true };
      }
      return player;
    }));
    nextPlayer();
  };

  // Следующий игрок
  const nextPlayer = () => {
    let nextIndex = (currentPlayerIndex + 1) % players.length;
    
    // Найдём следующего незавершившего игрока
    while (nextIndex !== currentPlayerIndex && players[nextIndex].isFinished) {
      nextIndex = (nextIndex + 1) % players.length;
    }

    // Если все закончили, показываем результаты
    if (players.every(p => p.isFinished || p.isBusted)) {
      endGame();
    } else {
      setCurrentPlayerIndex(nextIndex);
      setTimer(15);
    }
  };

  // Завершение игры
  const endGame = () => {
    const validPlayers = players.filter(p => !p.isBusted);
    const maxScore = Math.max(...validPlayers.map(p => p.score));
    
    const updatedPlayers = players.map(player => ({
      ...player,
      isWinner: !player.isBusted && player.score === maxScore
    }));

    setPlayers(updatedPlayers);
    setGameState('results');
  };

  // Новая игра
  const newGame = () => {
    setGameState('waiting');
    setPlayers(prev => prev.map(p => ({
      ...p,
      cards: [],
      score: 0,
      isActive: false,
      isFinished: false,
      isBusted: false,
      isWinner: false
    })));
  };

  // Компонент карты
  const CardComponent: React.FC<{ card: Card; isHidden?: boolean }> = ({ card, isHidden }) => (
    <div className={`w-16 h-24 rounded-lg flex flex-col items-center justify-center text-sm font-bold shadow-lg ${
      isHidden 
        ? 'bg-blue-600 text-white' 
        : card.suit === '♥' || card.suit === '♦' 
          ? 'bg-white text-red-600' 
          : 'bg-white text-black'
    }`}>
      {isHidden ? (
        <div className="text-2xl">🂠</div>
      ) : (
        <>
          <div className="text-lg">{card.value}</div>
          <div className="text-xl">{card.suit}</div>
        </>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-500 via-green-600 to-emerald-500 relative overflow-hidden">
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
              Карты 21
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
              <div className="text-6xl mb-6">🃏</div>
              <h2 className="text-2xl font-bold text-white mb-4">
                Готовы к игре в 21?
              </h2>
              <p className="text-white/80 mb-8">
                Наберите как можно ближе к 21, не превышая этот лимит!
              </p>
              <button
                onClick={dealInitialCards}
                className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-8 py-4 rounded-2xl font-bold text-lg hover:from-yellow-500 hover:to-orange-600 transition-all duration-300 transform hover:scale-105 shadow-xl flex items-center gap-3 mx-auto"
              >
                <FaPlay />
                Раздать карты!
              </button>
            </div>
          </div>
        )}

        {/* Индикатор хода */}
        {gameState === 'playing' && (
          <div className="text-center mb-8">
            <div className="glass-effect rounded-2xl p-4 max-w-sm mx-auto border border-white/20">
              <div className="text-white font-semibold">
                Ход игрока: {players[currentPlayerIndex]?.name}
              </div>
              <div className="text-white/70 text-sm">
                Осталось времени: {timer}с
              </div>
            </div>
          </div>
        )}

        {/* Сетка игроков */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {players.map((player, index) => (
            <div
              key={player.id}
              className={`glass-effect rounded-3xl p-6 border transition-all duration-300 ${
                player.isWinner 
                  ? 'border-yellow-400 bg-gradient-to-br from-yellow-400/20 to-orange-400/20' 
                  : index === currentPlayerIndex && gameState === 'playing'
                    ? 'border-blue-400 bg-gradient-to-br from-blue-400/20 to-purple-400/20'
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
                {player.isBusted && (
                  <div className="text-red-400 text-sm font-semibold">Перебор! 💥</div>
                )}
                {index === currentPlayerIndex && gameState === 'playing' && !player.isFinished && (
                  <div className="text-blue-400 text-sm font-semibold">Ваш ход! ⏰</div>
                )}
              </div>

              {/* Карты */}
              <div className="flex flex-wrap justify-center gap-2 mb-4 min-h-[100px]">
                {player.cards.map((card, cardIndex) => (
                  <CardComponent 
                    key={cardIndex} 
                    card={card}
                    isHidden={gameState === 'playing' && index !== 0} // Скрываем карты других игроков
                  />
                ))}
              </div>

              {/* Очки */}
              <div className="text-center mb-4">
                <div className={`text-2xl font-bold ${
                  player.isBusted ? 'text-red-400' : 'text-white'
                }`}>
                  {gameState === 'results' || index === 0 ? player.score : '?'}
                </div>
                <div className="text-white/70 text-sm">очков</div>
              </div>

              {/* Кнопки действий для текущего игрока */}
              {index === currentPlayerIndex && gameState === 'playing' && !player.isFinished && !player.isBusted && index === 0 && (
                <div className="flex gap-2 justify-center">
                  <button
                    onClick={hitCard}
                    className="bg-green-500 text-white px-4 py-2 rounded-xl hover:bg-green-600 transition-colors flex items-center gap-2"
                  >
                    <FaPlus />
                    Взять
                  </button>
                  <button
                    onClick={stand}
                    className="bg-red-500 text-white px-4 py-2 rounded-xl hover:bg-red-600 transition-colors flex items-center gap-2"
                  >
                    <FaStop />
                    Стоп
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Результаты игры */}
        {gameState === 'results' && (
          <div className="text-center mt-12">
            <div className="glass-effect rounded-3xl p-8 max-w-2xl mx-auto border border-white/20">
              <h2 className="text-3xl font-bold text-white mb-6">
                Результаты игры
              </h2>
              
              {(() => {
                const winners = players.filter(p => p.isWinner);
                const prizePerWinner = Math.floor(prizePool / winners.length);
                
                return (
                  <div className="text-center">
                    <div className="text-xl text-white/90 mb-4">
                      {winners.length === 1 
                        ? `🎉 Поздравляем ${winners[0].name}!`
                        : `🎉 Ничья! ${winners.length} победителя!`
                      }
                    </div>
                    <div className="text-lg text-yellow-400 font-semibold mb-8">
                      Каждый победитель получает: {prizePerWinner} ⭐
                    </div>
                    
                    <button
                      onClick={newGame}
                      className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-2xl font-bold text-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-xl"
                    >
                      Играть ещё
                    </button>
                  </div>
                );
              })()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CardsGame;
