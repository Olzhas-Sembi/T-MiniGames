import { useEffect, useState } from "react";
import TelegramService from "@/services/telegramService";

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
      <div style={{color: '#fff', background: '#181818', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
        <div>Проверка окружения...</div>
        <div style={{marginTop: 16, fontSize: 14}}>
          window.Telegram: {String(hasTelegram)}<br/>
          window.Telegram.WebApp: {String(hasWebApp)}
        </div>
      </div>
    );
  }
  if (isTelegram === false) {
    return (
      <div style={{color: '#fff', background: '#181818', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
        <div>Не Telegram Mini App</div>
        <div style={{marginTop: 16, fontSize: 14}}>
          window.Telegram: {String(hasTelegram)}<br/>
          window.Telegram.WebApp: {String(hasWebApp)}
        </div>
      </div>
    );
  }
  return (
    <div style={{color: '#fff', background: '#181818', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
      <div>Приложение успешно определено как Telegram Mini App!</div>
      <div style={{marginTop: 16, fontSize: 14}}>
        window.Telegram: {String(hasTelegram)}<br/>
        window.Telegram.WebApp: {String(hasWebApp)}<br/>
        isTelegram: {String(isTelegram)}
      </div>
    </div>
  );
};

export default App;