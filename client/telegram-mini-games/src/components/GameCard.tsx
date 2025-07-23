import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface GameCardProps {
  title: string;
  description: string;
  players: string;
  minBet: number;
  icon: React.ReactNode;
  onPlay: () => void;
  className?: string;
  comingSoon?: boolean;
  style?: React.CSSProperties;
}

export const GameCard = ({ 
  title, 
  description, 
  players, 
  minBet, 
  icon, 
  onPlay, 
  className,
  comingSoon = false,
  style
}: GameCardProps) => {
  return (
    <Card className={cn("game-card group relative overflow-hidden", className)} style={style}>
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="text-4xl mb-2 group-hover:scale-110 transition-transform duration-300">
            {icon}
          </div>
          {comingSoon && (
            <Badge variant="secondary" className="bg-muted text-muted-foreground">
              Скоро
            </Badge>
          )}
        </div>
        <CardTitle className="text-xl font-bold text-foreground group-hover:text-primary transition-colors">
          {title}
        </CardTitle>
        <CardDescription className="text-muted-foreground text-sm">
          {description}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex justify-between items-center text-sm">
          <span className="text-muted-foreground">Игроки:</span>
          <span className="text-foreground font-medium">{players}</span>
        </div>
        
        <div className="flex justify-between items-center text-sm">
          <span className="text-muted-foreground">Мин. ставка:</span>
          <div className="flex items-center gap-1">
            <span className="text-primary font-semibold">{minBet}</span>
            <span className="text-primary">⭐</span>
          </div>
        </div>

        <Button 
          variant="gaming" 
          size="lg" 
          className="w-full mt-4" 
          onClick={(e) => {
            console.log("Button clicked for game:", title);
            e.stopPropagation();
            e.preventDefault();
            console.log("About to call onPlay for:", title);
            onPlay();
          }}
          disabled={comingSoon}
        >
          {comingSoon ? "Скоро доступно" : "Играть"}
        </Button>
      </CardContent>
    </Card>
  );
};