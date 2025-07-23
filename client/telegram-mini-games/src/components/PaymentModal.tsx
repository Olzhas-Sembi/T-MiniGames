import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Star, Zap, QrCode, ExternalLink, Wallet, CreditCard, Gift } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { baseURL } from '../config';

interface PaymentMethod {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  enabled: boolean;
}

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (amount: number, method: string) => void;
  userBalance: number;
}

const PaymentModal: React.FC<PaymentModalProps> = ({ 
  isOpen, 
  onClose, 
  onSuccess, 
  userBalance 
}) => {
  const [selectedMethod, setSelectedMethod] = useState<string>('stars');
  const [amount, setAmount] = useState<number>(100);
  const [loading, setLoading] = useState(false);
  const [qrCode, setQrCode] = useState<string>('');
  const [paymentUrl, setPaymentUrl] = useState<string>('');
  const [exchangeRates, setExchangeRates] = useState({ ton_to_stars: 1000, stars_to_ton: 0.001 });

  const paymentMethods: PaymentMethod[] = [
    {
      id: 'stars',
      name: 'Telegram Stars',
      icon: <Star className="w-5 h-5" />,
      description: 'Оплата через Telegram Stars',
      enabled: true
    },
    {
      id: 'ton',
      name: 'TON Connect',
      icon: <Zap className="w-5 h-5" />,
      description: 'Оплата криптовалютой TON',
      enabled: true
    },
    {
      id: 'card',
      name: 'Банковская карта',
      icon: <CreditCard className="w-5 h-5" />,
      description: 'Оплата картой (скоро)',
      enabled: false
    }
  ];

  useEffect(() => {
    // Загружаем курсы обмена
    fetchExchangeRates();
  }, []);

  const fetchExchangeRates = async () => {
    try {
      const response = await fetch(`${baseURL}/api/payments/rates`);
      const data = await response.json();
      setExchangeRates(data);
    } catch (error) {
      console.error('Error fetching exchange rates:', error);
    }
  };

  const handlePayment = async () => {
    setLoading(true);
    try {
      if (selectedMethod === 'stars') {
        await handleStarsPayment();
      } else if (selectedMethod === 'ton') {
        await handleTonPayment();
      }
    } catch (error) {
      console.error('Payment error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStarsPayment = async () => {
    try {
      const userId = localStorage.getItem('userId') || 'user_123';
      
      const response = await fetch(`${baseURL}/api/payments/stars/create-invoice`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          amount_stars: amount,
          invoice_title: `Пополнение ${amount} звезд`,
          invoice_description: `Пополнение баланса на ${amount} звезд в Telegram Mini Games`,
          payload: `deposit_${Date.now()}`
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setPaymentUrl(data.payment_url);
        // Открываем Telegram для оплаты
        if (data.payment_url) {
          // Проверяем, что мы внутри Telegram WebApp
          const tgWebApp = window.Telegram && window.Telegram.WebApp ? (window.Telegram.WebApp as any) : null;
          if (tgWebApp && tgWebApp.openInvoice) {
            let slug = '';
            if (data.payment_url.startsWith('https://t.me/')) {
              // Ссылка может быть https://t.me/yourbot?start=pay_invoice_xxx или https://t.me/invoice/xxx
              if (data.payment_url.includes('?start=')) {
                slug = data.payment_url.split('?start=')[1];
              } else if (data.payment_url.includes('/invoice/')) {
                slug = data.payment_url.split('/invoice/')[1];
              }
            }
            if (slug) {
              tgWebApp.openInvoice(slug);
            } else {
              // fallback: открыть ссылку в новом окне
              window.open(data.payment_url, '_blank');
            }
          } else {
            // Если не в Telegram WebApp, просто открыть ссылку
            window.open(data.payment_url, '_blank');
          }
        }
        onSuccess(amount, 'stars');
      } else {
        throw new Error(data.message || 'Payment creation failed');
      }
    } catch (error) {
      console.error('Stars payment error:', error);
      throw error;
    }
  };

  const handleTonPayment = async () => {
    try {
      const userId = localStorage.getItem('userId') || 'user_123';
      const tonAmount = amount * exchangeRates.stars_to_ton;
      
      const response = await fetch(`${baseURL}/api/payments/ton/create-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          amount_ton: tonAmount,
          destination_address: 'EQD-cvR0Nz6XAyRBpDYmy3g5dLKq5U9F6vJQf-nCUH6XTNG', // Адрес получателя
          wallet_address: 'user_wallet_address' // Адрес пользователя
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setPaymentUrl(data.payment_url);
        setQrCode(data.qr_code);
        onSuccess(amount, 'ton');
      } else {
        throw new Error(data.message || 'TON payment creation failed');
      }
    } catch (error) {
      console.error('TON payment error:', error);
      throw error;
    }
  };

  const openTelegramInvoice = () => {
    const tgWebApp = window.Telegram && window.Telegram.WebApp ? (window.Telegram.WebApp as any) : null;
    if (tgWebApp && tgWebApp.openInvoice) {
      tgWebApp.openInvoice({
        slug: '', // если есть slug, иначе можно payload
        invoice: {
          provider_token: 'test', // для теста, в реальности сюда приходит invoice от бэка
          start_parameter: 'test-pay',
          currency: 'RUB',
          prices: [{ label: 'Тестовый товар', amount: 10000 }],
          title: 'Тестовая оплата',
          description: 'Покупка тестового товара',
          payload: 'test-payload',
        }
      });
    } else {
      alert('Оплата доступна только в Telegram Mini App');
    }
  };

  const presetAmounts = [100, 500, 1000, 2500, 5000, 10000];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wallet className="w-5 h-5" />
            Пополнение баланса
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Текущий баланс */}
          <Card className="bg-gradient-to-r from-primary/10 to-accent/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Текущий баланс</span>
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-primary" />
                  <span className="font-bold">{userBalance}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Выбор суммы */}
          <div className="space-y-3">
            <label className="text-sm font-medium">Сумма пополнения</label>
            
            {/* Готовые суммы */}
            <div className="grid grid-cols-3 gap-2">
              {presetAmounts.map((preset) => (
                <Button
                  key={preset}
                  variant={amount === preset ? "default" : "outline"}
                  size="sm"
                  onClick={() => setAmount(preset)}
                  className="flex items-center gap-1"
                >
                  <Star className="w-3 h-3" />
                  {preset}
                </Button>
              ))}
            </div>

            {/* Произвольная сумма */}
            <Input
              type="number"
              placeholder="Введите сумму"
              value={amount}
              onChange={(e) => setAmount(parseInt(e.target.value) || 0)}
              min={1}
              max={100000}
            />
          </div>

          {/* Способы оплаты */}
          <Tabs value={selectedMethod} onValueChange={setSelectedMethod}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="stars" className="flex items-center gap-2">
                <Star className="w-4 h-4" />
                Stars
              </TabsTrigger>
              <TabsTrigger value="ton" className="flex items-center gap-2">
                <Zap className="w-4 h-4" />
                TON
              </TabsTrigger>
            </TabsList>

            <TabsContent value="stars" className="space-y-3">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Star className="w-8 h-8 text-yellow-500" />
                    <div>
                      <h4 className="font-medium">Telegram Stars</h4>
                      <p className="text-sm text-muted-foreground">
                        Быстрая оплата через Telegram
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="ton" className="space-y-3">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Zap className="w-8 h-8 text-blue-500" />
                    <div>
                      <h4 className="font-medium">TON Connect</h4>
                      <p className="text-sm text-muted-foreground">
                        {amount} ⭐ = {(amount * exchangeRates.stars_to_ton).toFixed(4)} TON
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* QR код для TON */}
          <AnimatePresence>
            {qrCode && selectedMethod === 'ton' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="text-center space-y-3"
              >
                <img src={qrCode} alt="QR Code" className="mx-auto w-48 h-48" />
                <p className="text-sm text-muted-foreground">
                  Отсканируйте QR код кошельком TON
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Кнопка оплаты */}
          <div className="space-y-3">
            <Button
              onClick={handlePayment}
              disabled={loading || amount <= 0}
              className="w-full"
              size="lg"
            >
              {loading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
                />
              ) : (
                <>
                  <Star className="w-4 h-4 mr-2" />
                  Пополнить на {amount} ⭐
                </>
              )}
            </Button>

            {paymentUrl && (
              <Button
                variant="outline"
                onClick={() => window.open(paymentUrl, '_blank')}
                className="w-full"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Открыть ссылку для оплаты
              </Button>
            )}
            <Button onClick={openTelegramInvoice}>Оплатить картой через Telegram</Button>
          </div>

          {/* Информация */}
          <div className="text-xs text-muted-foreground space-y-1">
            <p>• Звезды зачисляются автоматически после оплаты</p>
            <p>• Минимальная сумма: 1 ⭐</p>
            <p>• Максимальная сумма: 100,000 ⭐</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PaymentModal;
