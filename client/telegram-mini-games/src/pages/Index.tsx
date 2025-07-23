import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { GameCard } from "@/components/GameCard";
import { UserProfile } from "@/components/UserProfile";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dice1, Scissors, Square, Gift, Package, Sparkles, Users, TrendingUp } from "lucide-react";
import heroImage from "@/assets/gaming-hero.jpg";
import { NewsAggregator } from "@/components/NewsAggregator";

const Index = () => {
  const navigate = useNavigate();
  const [userBalance, setUserBalance] = useState(2500);

  const games = [
    {
      title: "Кубики",
      description: "Бросайте кубики и выигрывайте! Самая высокая сумма побеждает.",
      players: "2-4",
      minBet: 100,
      icon: <Dice1 className="w-8 h-8 text-primary" />,
      onPlay: () => {
        console.log("Navigating to dice game");
        navigate("/dice-game");
      }
    },
    {
      title: "Камень-Ножницы-Бумага", 
      description: "Классическая игра для всех возрастов с новыми правилами.",
      players: "2-4",
      minBet: 50,
      icon: <Scissors className="w-8 h-8 text-primary" />,
      onPlay: () => {
        console.log("Navigating to rps game");
        navigate("/rps-game");
      }
    },
    {
      title: "Карты 21",
      description: "Наберите как можно ближе к 21, но не перебирайте!",
      players: "2-4", 
      minBet: 200,
      icon: <Square className="w-8 h-8 text-primary" />,
      onPlay: () => {},
      comingSoon: true
    },
    {
      title: "Лото 3×3",
      description: "Соберите три в ряд быстрее соперников!",
      players: "2-4",
      minBet: 150,
      icon: <Gift className="w-8 h-8 text-primary" />,
      onPlay: () => {},
      comingSoon: true
    },
    {
      title: "Case Battle",
      description: "Открывайте кейсы и соревнуйтесь за самые ценные NFT!",
      players: "2-4",
      minBet: 500,
      icon: <Package className="w-8 h-8 text-primary" />,
      onPlay: () => {},
      comingSoon: true
    },
    {
      title: "Рулетка-Розыгрыш",
      description: "Коллективные розыгрыши крутых призов!",
      players: "Без лимита",
      minBet: 100,
      icon: <Sparkles className="w-8 h-8 text-primary" />,
      onPlay: () => {},
      comingSoon: true
    }
  ];

  const handleAddFunds = () => {
    // Временная заглушка для пополнения
    setUserBalance(prev => prev + 1000);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div 
          className="h-96 bg-cover bg-center bg-no-repeat relative"
          style={{ backgroundImage: `url(${heroImage})` }}
        >
          <div className="absolute inset-0 bg-black/50" />
          <div className="relative z-10 flex items-center justify-center h-full text-center">
            <div className="max-w-4xl px-4">
              <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 animate-fade-in">
                Игровая платформа
              </h1>
              <p className="text-xl md:text-2xl text-white/90 mb-8 animate-slide-up">
                Мини-игры с живыми лобби, честной механикой и реальными призами
              </p>
              <div className="flex flex-wrap justify-center gap-4 animate-slide-up">
                <Button variant="gaming" size="xl" onClick={() => document.getElementById('games-section')?.scrollIntoView({ behavior: 'smooth' })}>
                  <Users className="w-5 h-5 mr-2" />
                  Выбрать игру
                </Button>
                <Button variant="outline" size="xl" className="bg-white/10 border-white/20 text-white hover:bg-white/20" onClick={() => navigate("/lobby")}>
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Лобби игр
                </Button>
                <Button variant="outline" size="xl" className="bg-purple-500/20 border-purple-400/30 text-white hover:bg-purple-500/30" onClick={() => navigate("/nft")}>
                  <Package className="w-5 h-5 mr-2" />
                  NFT Коллекция
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-8">
        {/* User Profile Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <UserProfile
              username="Player123"
              balance={userBalance}
              totalGames={42}
              wins={28}
              onAddFunds={handleAddFunds}
              onTonDeposit={() => alert("TON deposit")}
              onTelegramDeposit={() => alert("Telegram deposit")}
              transactions={[]}
            />
          </div>
          
          {/* Stats Cards */}
          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="game-card">
              <CardContent className="p-6 text-center">
                <Users className="w-8 h-8 text-primary mx-auto mb-2" />
                <div className="text-2xl font-bold text-foreground">1,247</div>
                <div className="text-sm text-muted-foreground">Активных игроков</div>
              </CardContent>
            </Card>
            
            <Card className="game-card">
              <CardContent className="p-6 text-center">
                <Sparkles className="w-8 h-8 text-accent mx-auto mb-2" />
                <div className="text-2xl font-bold text-foreground">15</div>
                <div className="text-sm text-muted-foreground">Активных лобби</div>
              </CardContent>
            </Card>
          </div>
        </div>
        
        {/* Games Section */}
        <div id="games-section" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-3xl font-bold text-foreground">Выберите игру</h2>
            <Badge variant="secondary" className="text-sm">
              6 режимов
            </Badge>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {games.map((game, index) => (
              <GameCard
                key={game.title}
                {...game}
                className={`animate-fade-in`}
                style={{ animationDelay: `${index * 0.1}s` } as React.CSSProperties}
              />
            ))}
          </div>
        </div>
        < NewsAggregator />
        {/* Features Section */}
        <Card className="game-card mt-12">
          <CardContent className="p-8">
            <h3 className="text-2xl font-bold text-foreground mb-6 text-center">
              Почему выбирают нашу платформу?
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mx-auto">
                  <Users className="w-6 h-6 text-primary" />
                </div>
                <h4 className="font-semibold text-foreground">Живые лобби</h4>
                <p className="text-sm text-muted-foreground">
                  Играйте с реальными людьми в режиме реального времени
                </p>
              </div>
              
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center mx-auto">
                  <Sparkles className="w-6 h-6 text-accent" />
                </div>
                <h4 className="font-semibold text-foreground">Честная игра</h4>
                <p className="text-sm text-muted-foreground">
                  Криптографические доказательства честности всех игр
                </p>
              </div>
              
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mx-auto">
                  <Package className="w-6 h-6 text-primary" />
                </div>
                <h4 className="font-semibold text-foreground">NFT призы</h4>
                <p className="text-sm text-muted-foreground">
                  Выигрывайте уникальные NFT и редкие предметы
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Index;
