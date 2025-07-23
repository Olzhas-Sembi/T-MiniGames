import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import { GameLobby } from "./pages/GameLobby";
import NotFound from "./pages/NotFound";
import DiceGamePage from "./pages/DiceGamePage";
import RPSGamePage from "./pages/RPSGamePage";
import NFTPage from "./pages/NFTPage";
import TelegramService from "@/services/telegramService";
import { useEffect, useState } from "react";

const queryClient = new QueryClient();

const App = () => {
  const [isTelegram, setIsTelegram] = useState<boolean | null>(null);

  useEffect(() => {
    let attempts = 0;
    function checkTelegram() {
      if (TelegramService.isInTelegram()) {
        setIsTelegram(true);
        TelegramService.init();
      } else if (attempts < 10) {
        attempts++;
        setTimeout(checkTelegram, 200);
      } else {
        setIsTelegram(false);
      }
    }
    checkTelegram();
  }, []);

  if (isTelegram === false) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", background: "#181818", color: "#fff" }}>
        <h2 style={{ fontSize: 28, marginBottom: 16 }}>Откройте мини-приложение через Telegram</h2>
        <p style={{ fontSize: 18, opacity: 0.8 }}>Данное приложение доступно только внутри Telegram Mini Apps.<br/>Пожалуйста, откройте его через Telegram.</p>
      </div>
    );
  }

  if (isTelegram === null) {
    // Можно добавить спиннер или оставить пусто
    return null;
  }

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/lobby" element={<GameLobby />} />
            <Route path="/dice-game" element={<DiceGamePage />} />
            <Route path="/rps-game" element={<RPSGamePage />} />
            <Route path="/nft" element={<NFTPage />} />
            <Route path="/game/dice/:lobbyId" element={<DiceGamePage />} />
            <Route path="/game/rps/:lobbyId" element={<RPSGamePage />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;