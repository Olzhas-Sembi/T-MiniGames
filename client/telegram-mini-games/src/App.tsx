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
import TelegramService from "@/services/telegramService";
import { useEffect, useState } from "react";

const queryClient = new QueryClient();

const App = () => {
  const [isTelegram, setIsTelegram] = useState<boolean | null>(null);
  const [hasTelegram, setHasTelegram] = useState(false);
  const [hasWebApp, setHasWebApp] = useState(false);

  useEffect(() => {
    let attempts = 0;
    function checkTelegram() {
      setHasTelegram(typeof window !== 'undefined' && !!window.Telegram);
      setHasWebApp(typeof window !== 'undefined' && !!window.Telegram?.WebApp);

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

  if (isTelegram === null) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", justifyContent: "center", alignItems: "center", background: "#181818", color: "#fff" }}>
        <span>Загрузка...</span>
      </div>
    );
  }

  if (isTelegram === false) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", background: "#181818", color: "#fff" }}>
        <h2 style={{ fontSize: 28, marginBottom: 16 }}>Откройте мини-приложение через Telegram</h2>
        <p style={{ fontSize: 18, opacity: 0.8 }}>Данное приложение доступно только внутри Telegram Mini Apps.<br/>Пожалуйста, откройте его через Telegram.</p>
        <div style={{marginTop: 16, fontSize: 14}}>
          window.Telegram: {String(hasTelegram)}<br/>
          window.Telegram.WebApp: {String(hasWebApp)}<br/>
        </div>
      </div>
    );
  }

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
