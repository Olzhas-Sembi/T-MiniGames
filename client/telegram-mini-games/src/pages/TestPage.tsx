import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

const TestPage = () => {
  const navigate = useNavigate();

  const testNavigation = () => {
    console.log("Test navigation - going to dice game");
    navigate("/dice-game");
  };

  const testNavigation2 = () => {
    console.log("Test navigation - going to rps game");
    navigate("/rps-game");
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-2xl mx-auto space-y-4">
        <h1 className="text-3xl font-bold">Test Navigation</h1>
        
        <div className="space-y-4">
          <Button onClick={testNavigation} className="w-full">
            Test Dice Game Navigation
          </Button>
          
          <Button onClick={testNavigation2} className="w-full">
            Test RPS Game Navigation
          </Button>
          
          <Button onClick={() => navigate("/")} variant="outline" className="w-full">
            Back to Home
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TestPage;
