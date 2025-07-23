import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Star, Trophy, Gamepad2, Plus } from "lucide-react";

interface UserProfileProps {
  username: string;
  balance: number;
  totalGames: number;
  wins: number;
  onAddFunds: () => void;
  onTonDeposit: () => void;
  onTelegramDeposit: () => void;
  transactions: Array<{
    id: string;
    type: string;
    amount: number;
    status?: string;
    created_at: string;
    description?: string;
  }>;
}

export const UserProfile = ({ 
  username, 
  balance, 
  totalGames, 
  wins, 
  onAddFunds,
  onTonDeposit,
  onTelegramDeposit,
  transactions
}: UserProfileProps) => {
  const winRate = totalGames > 0 ? Math.round((wins / totalGames) * 100) : 0;

  return (
    <Card className="game-card">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl font-bold text-foreground flex items-center gap-2">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-lg">
            {username.charAt(0).toUpperCase()}
          </div>
          {username}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-primary/10 to-accent/10 border border-primary/20">
          <div className="flex items-center gap-2">
            <Star className="w-5 h-5 text-primary" />
            <span className="text-lg font-semibold text-foreground">Баланс</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-2xl font-bold text-primary">{balance}</span>
            <Star className="w-6 h-6 text-primary" />
          </div>
        </div>

        <div className="flex gap-2">
          <Button 
            variant="gaming" 
            size="lg" 
            className="w-1/2" 
            onClick={onTonDeposit}
          >
            <Plus className="w-4 h-4 mr-2" />
            Депозит TON
          </Button>
          <Button 
            variant="outline" 
            size="lg" 
            className="w-1/2" 
            onClick={onTelegramDeposit}
          >
            <Plus className="w-4 h-4 mr-2" />
            Telegram
          </Button>
        </div>

        <Button 
          variant="secondary" 
          size="lg" 
          className="w-full" 
          onClick={onAddFunds}
        >
          <Plus className="w-4 h-4 mr-2" />
          Пополнить (заглушка)
        </Button>

        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="space-y-1">
            <div className="flex items-center justify-center">
              <Gamepad2 className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="text-lg font-semibold text-foreground">{totalGames}</div>
            <div className="text-xs text-muted-foreground">Игр</div>
          </div>
          
          <div className="space-y-1">
            <div className="flex items-center justify-center">
              <Trophy className="w-4 h-4 text-primary" />
            </div>
            <div className="text-lg font-semibold text-foreground">{wins}</div>
            <div className="text-xs text-muted-foreground">Побед</div>
          </div>
          
          <div className="space-y-1">
            <Badge variant="secondary" className="w-full py-1">
              {winRate}%
            </Badge>
            <div className="text-xs text-muted-foreground">Винрейт</div>
          </div>
        </div>

        {/* История транзакций */}
        <div className="mt-6">
          <div className="font-semibold mb-2 text-foreground">История транзакций</div>
          <div className="max-h-40 overflow-y-auto text-xs divide-y divide-muted-foreground/10">
            {transactions.length === 0 && <div className="text-muted-foreground">Нет транзакций</div>}
            {transactions.slice(0, 10).map(tx => (
              <div key={tx.id} className="flex justify-between py-1 items-center">
                <span className="font-mono">{tx.type}</span>
                <span className={tx.amount > 0 ? "text-green-600" : "text-red-600"}>{tx.amount > 0 ? "+" : ""}{tx.amount}</span>
                <span className="text-muted-foreground">{tx.status || "-"}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};