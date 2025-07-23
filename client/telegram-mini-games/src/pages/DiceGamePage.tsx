import DiceGame from "@/games/dice/DiceGame";
import { useNavigate } from "react-router-dom";

const DiceGamePage = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto p-6">
        <DiceGame 
          onBack={() => navigate("/")}
          playerName="Player"
          playerId="1"
          websocket={null}
          roomData={null}
        />
      </div>
    </div>
  );
};

export default DiceGamePage;