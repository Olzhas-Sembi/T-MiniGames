import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LobbyCard } from "@/components/LobbyCard";
import { ArrowLeft, Users, Clock, RefreshCw } from "lucide-react";
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

  useEffect(() => {
    const timer = setInterval(() => {
      setLobbies(prev => prev.map(lobby => ({
        ...lobby,
        timeLeft: Math.max(0, lobby.timeLeft - 1)
      })).filter(lobby => lobby.timeLeft > 0));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleCreateLobby = () => {
    setIsSearching(true);
    setTimeout(() => {
      const newLobby: Lobby = {
        id: `lobby-${Date.now()}`,
        gameType: "Кубики",
        currentPlayers: 1,
        maxPlayers: 4,
        bet: 100,
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
          <Button 
            variant="gaming" 
            onClick={handleCreateLobby}
            disabled={isSearching}
            className="min-w-[140px]"
          >
            {isSearching ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Поиск...
              </>
            ) : (
              "Создать лобби"
            )}
          </Button>
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
                  onJoin={() => handleJoinLobby(lobby.id)}
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
                <Button variant="gaming" onClick={handleCreateLobby}>
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