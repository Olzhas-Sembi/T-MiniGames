import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, Clock, Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface LobbyCardProps {
  id: string;
  gameType: string;
  currentPlayers: number;
  maxPlayers: number;
  bet: number;
  timeLeft: number;
  host: string;
  onJoin: () => void;
  className?: string;
}

export const LobbyCard = ({ 
  id, 
  gameType, 
  currentPlayers, 
  maxPlayers, 
  bet, 
  timeLeft, 
  host, 
  onJoin,
  className 
}: LobbyCardProps) => {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const isAlmostFull = currentPlayers >= maxPlayers - 1;

  return (
    <Card className={cn("game-card hover:border-primary/50 transition-all duration-300", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-foreground">
            {gameType}
          </CardTitle>
          <Badge 
            variant={isAlmostFull ? "default" : "secondary"} 
            className={isAlmostFull ? "bg-primary animate-pulse" : ""}
          >
            ID: {id.slice(-4)}
          </Badge>
        </div>
        <div className="text-sm text-muted-foreground">
          Хост: {host}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="flex items-center gap-1">
            <Users className="w-4 h-4 text-primary" />
            <span className="text-foreground font-medium">
              {currentPlayers}/{maxPlayers}
            </span>
          </div>
          
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4 text-accent" />
            <span className="text-foreground font-medium">
              {formatTime(timeLeft)}
            </span>
          </div>
          
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 text-primary" />
            <span className="text-foreground font-medium">
              {bet}
            </span>
          </div>
        </div>

        <div className="w-full bg-muted rounded-full h-2">
          <div 
            className="bg-primary h-2 rounded-full transition-all duration-300"
            style={{ width: `${(currentPlayers / maxPlayers) * 100}%` }}
          />
        </div>

        <Button 
          variant="lobby" 
          size="sm" 
          className="w-full" 
          onClick={onJoin}
          disabled={currentPlayers >= maxPlayers}
        >
          {currentPlayers >= maxPlayers ? "Лобби заполнено" : "Присоединиться"}
        </Button>
      </CardContent>
    </Card>
  );
};