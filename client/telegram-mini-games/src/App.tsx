import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import { GameLobby } from "./pages/GameLobby";
import NotFound from "./pages/NotFound";
import DiceGamePage from "./pages/DiceGamePage";
import RPSGamePage from "./pages/RPSGamePage";
import NFTPage from "./pages/NFTPage";
// import TelegramService from "@/services/telegramService";
import { useEffect, useState } from "react";

const queryClient = new QueryClient();

const App = () => {
  // Временно убираем проверку на Telegram
  // const [isTelegram, setIsTelegram] = useState<boolean | null>(null);
  // useEffect(() => {
  //   if (window.location.hash === "#/startapp") {
  //     window.location.hash = "#/";
  //   }
  //   let attempts = 0;
  //   function checkTelegram() {
  //     if (TelegramService.isInTelegram()) {
  //       setIsTelegram(true);
  //       TelegramService.init();
  //     } else if (attempts < 10) {
  //       attempts++;
  //       setTimeout(checkTelegram, 200);
  //     } else {
  //       setIsTelegram(false);
  //     }
  //   }
  //   checkTelegram();
  // }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <HashRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/lobby" element={<GameLobby />} />
            <Route path="/dice-game" element={<DiceGamePage />} />
            <Route path="/rps-game" element={<RPSGamePage />} />
            <Route path="/nft" element={<NFTPage />} />
            <Route path="/game/dice/:lobbyId" element={<DiceGamePage />} />
            <Route path="/game/rps/:lobbyId" element={<RPSGamePage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </HashRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
