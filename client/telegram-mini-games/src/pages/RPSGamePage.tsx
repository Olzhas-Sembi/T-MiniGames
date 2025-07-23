import RockPaperScissors from "@/games/rps/RockPaperScissors";
import { useNavigate } from "react-router-dom";

const RPSGamePage = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto p-6">
        <RockPaperScissors playerName="Player123" onBack={() => navigate("/")} />
      </div>
    </div>
  );
};

export default RPSGamePage;