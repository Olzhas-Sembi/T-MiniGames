import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { LobbyCard } from "@/components/LobbyCard";
import { ArrowLeft, Users, Clock, RefreshCw, Dice1, Scissors } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface Lobby {
  id: string;
  gameType: string;
  currentPlayers: number;
  maxPlayers: number;
  bet: number;
  timeLeft: number;
  host: string;
}

export const GameLobby = () => {
  const navigate = useNavigate();
  const [lobbies, setLobbies] = useState<Lobby[]>([
    {
      id: "lobby-1",
      gameType: "Кубики",
      currentPlayers: 2,
      maxPlayers: 4,
      bet: 100,
      timeLeft: 45,
      host: "Player123"
    },
    {
      id: "lobby-2", 
      gameType: "Камень-Ножницы-Бумага",
      currentPlayers: 1,
      maxPlayers: 4,
      bet: 200,
      timeLeft: 55,
      host: "GamerPro"
    },
    {
      id: "lobby-3",
      gameType: "Кубики",
      currentPlayers: 3,
      maxPlayers: 4,
      bet: 150,
      timeLeft: 30,
      host: "Winner99"
    }
  ]);

  const [isSearching, setIsSearching] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const gameTypes = [
    { name: "Кубики", icon: <Dice1 className="w-6 h-6" />, minBet: 100 },
    { name: "Камень-Ножницы-Бумага", icon: <Scissors className="w-6 h-6" />, minBet: 50 }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setLobbies(prev => prev.map(lobby => ({
        ...lobby,
        timeLeft: Math.max(0, lobby.timeLeft - 1)
      })).filter(lobby => lobby.timeLeft > 0));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleCreateLobby = (gameType: string, minBet: number) => {
    setIsSearching(true);
    setShowCreateDialog(false);
    setTimeout(() => {
      const newLobby: Lobby = {
        id: `lobby-${Date.now()}`,
        gameType: gameType,
        currentPlayers: 1,
        maxPlayers: 4,
        bet: minBet,
        timeLeft: 60,
        host: "Вы"
      };
      setLobbies(prev => [...prev, newLobby]);
      setIsSearching(false);
    }, 2000);
  };

  const handleJoinLobby = (lobbyId: string) => {
    setLobbies(prev => prev.map(lobby => 
      lobby.id === lobbyId 
        ? { ...lobby, currentPlayers: Math.min(lobby.currentPlayers + 1, lobby.maxPlayers) }
        : lobby
    ));
  };

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button 
            variant="ghost" 
            onClick={() => navigate("/")}
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Назад
          </Button>
          <h1 className="text-3xl font-bold text-foreground">Игровые лобби</h1>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button 
                variant="gaming" 
                disabled={isSearching}
                className="min-w-[140px]"
              >
                {isSearching ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Создание...
                  </>
                ) : (
                  "Создать лобби"
                )}
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Выберите игру</DialogTitle>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {gameTypes.map((game) => (
                  <Button
                    key={game.name}
                    variant="outline"
                    className="h-16 flex items-center justify-start gap-4 p-4"
                    onClick={() => handleCreateLobby(game.name, game.minBet)}
                  >
                    {game.icon}
                    <div className="text-left">
                      <div className="font-semibold">{game.name}</div>
                      <div className="text-sm text-muted-foreground">Мин. ставка: {game.minBet} ⭐</div>
                    </div>
                  </Button>
                ))}
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <Card className="game-card">
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              <div className="space-y-2">
                <div className="flex items-center justify-center">
                  <Users className="w-6 h-6 text-primary" />
                </div>
                <div className="text-2xl font-bold text-foreground">{lobbies.length}</div>
                <div className="text-sm text-muted-foreground">Активных лобби</div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-center">
                  <Clock className="w-6 h-6 text-accent" />
                </div>
                <div className="text-2xl font-bold text-foreground">
                  {lobbies.reduce((acc, lobby) => acc + lobby.currentPlayers, 0)}
                </div>
                <div className="text-sm text-muted-foreground">Игроков онлайн</div>
              </div>
              
              <div className="space-y-2">
                <Badge variant="secondary" className="text-lg px-4 py-2">
                  {Math.round(lobbies.reduce((acc, lobby) => acc + lobby.currentPlayers, 0) / Math.max(lobbies.length, 1) * 25)}%
                </Badge>
                <div className="text-sm text-muted-foreground">Заполненность</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Active Lobbies */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground">Доступные лобби</h2>
          
          {lobbies.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {lobbies.map((lobby) => (
                <LobbyCard
                  key={lobby.id}
                  {...lobby}
                  onJoin={() => {
                    if (lobby.gameType === "Кубики") {
                      navigate(`/game/dice/${lobby.id}`);
                    } else if (lobby.gameType === "Камень-Ножницы-Бумага") {
                      navigate(`/game/rps/${lobby.id}`);
                    }
                  }}
                  className="animate-fade-in"
                />
              ))}
            </div>
          ) : (
            <Card className="game-card text-center py-12">
              <CardContent>
                <div className="text-muted-foreground mb-4">
                  <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  Нет активных лобби
                </div>
                <Button variant="gaming" onClick={() => setShowCreateDialog(true)}>
                  Создать первое лобби
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};