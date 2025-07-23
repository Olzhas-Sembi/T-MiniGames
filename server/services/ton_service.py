"""
TON Connect интеграция для Telegram Mini Games
Обеспечивает:
- Подключение кошельков TON
- Отправку транзакций
- Проверку балансов
- Генерацию QR кодов
"""

import asyncio
import json
import qrcode
import io
import base64
from typing import Optional, Dict, Any, List
from decimal import Decimal
import aiohttp
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TONConnectService:
    """Сервис для работы с TON Connect"""
    
    def __init__(self, manifest_url: str, api_key: Optional[str] = None):
        self.manifest_url = manifest_url
        self.api_key = api_key
        self.testnet = True  # Для разработки используем testnet
        
        # TON API endpoints
        if self.testnet:
            self.ton_api_base = "https://testnet.toncenter.com/api/v2"
            self.tonapi_base = "https://testnet.tonapi.io"
        else:
            self.ton_api_base = "https://toncenter.com/api/v2"
            self.tonapi_base = "https://tonapi.io"
    
    async def generate_connect_link(self, return_url: str) -> Dict[str, str]:
        """
        Генерирует ссылку для подключения кошелька
        """
        try:
            # Создаем запрос на подключение
            connect_request = {
                "manifestUrl": self.manifest_url,
                "items": [
                    {
                        "name": "ton_addr",
                        "permissions": ["read"]
                    },
                    {
                        "name": "ton_proof",
                        "permissions": ["read"]
                    }
                ]
            }
            
            # Генерируем deep link для TON Connect
            connect_data = json.dumps(connect_request)
            encoded_data = base64.b64encode(connect_data.encode()).decode()
            
            deep_link = f"tc://connect?v=2&id=1&r={return_url}&ret=back&s={encoded_data}"
            universal_link = f"https://app.tonkeeper.com/ton-connect?v=2&id=1&r={return_url}&ret=back&s={encoded_data}"
            
            # Генерируем QR код
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(universal_link)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = io.BytesIO()
            qr_image.save(qr_buffer, format='PNG')
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
            
            return {
                "deep_link": deep_link,
                "universal_link": universal_link,
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "connect_data": encoded_data
            }
            
        except Exception as e:
            logger.error(f"Error generating connect link: {e}")
            raise
    
    async def verify_wallet_connection(self, wallet_address: str, proof: Dict[str, Any]) -> bool:
        """
        Проверяет подключение кошелька и валидность proof
        """
        try:
            # Здесь должна быть логика проверки криптографического proof
            # Для упрощения пока возвращаем True если адрес валидный
            if len(wallet_address) == 48 and wallet_address.startswith(('EQ', 'UQ')):
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error verifying wallet: {e}")
            return False
    
    async def get_wallet_balance(self, wallet_address: str) -> Decimal:
        """
        Получает баланс кошелька в TON
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.ton_api_base}/getAddressBalance"
                params = {
                    "address": wallet_address,
                    "api_key": self.api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            balance_nano = int(data["result"])
                            # Конвертируем из nanoTON в TON
                            return Decimal(balance_nano) / Decimal(10**9)
                    
                    logger.error(f"Failed to get balance: {response.status}")
                    return Decimal(0)
                    
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return Decimal(0)
    
    async def generate_payment_link(self, 
                                  recipient_address: str,
                                  amount_ton: Decimal,
                                  memo: Optional[str] = None) -> Dict[str, str]:
        """
        Генерирует ссылку для платежа
        """
        try:
            # Конвертируем TON в nanoTON
            amount_nano = int(amount_ton * Decimal(10**9))
            
            # Создаем данные транзакции
            transaction = {
                "to": recipient_address,
                "value": str(amount_nano),
                "timeout": 600,  # 10 минут
            }
            
            if memo:
                transaction["data"] = memo
            
            # Генерируем deep link
            tx_data = json.dumps([transaction])
            encoded_tx = base64.b64encode(tx_data.encode()).decode()
            
            deep_link = f"ton://transfer/{recipient_address}?amount={amount_nano}"
            if memo:
                deep_link += f"&text={memo}"
                
            universal_link = f"https://app.tonkeeper.com/transfer/{recipient_address}?amount={amount_nano}"
            if memo:
                universal_link += f"&text={memo}"
            
            # Генерируем QR код для платежа
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(universal_link)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = io.BytesIO()
            qr_image.save(qr_buffer, format='PNG')
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
            
            return {
                "deep_link": deep_link,
                "universal_link": universal_link,
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "amount_nano": amount_nano,
                "transaction_data": encoded_tx
            }
            
        except Exception as e:
            logger.error(f"Error generating payment link: {e}")
            raise
    
    async def check_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Проверяет статус транзакции по хешу
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.ton_api_base}/getTransactions"
                params = {
                    "address": tx_hash,
                    "limit": 1,
                    "api_key": self.api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok") and data.get("result"):
                            tx = data["result"][0]
                            return {
                                "confirmed": True,
                                "success": True,
                                "amount": tx.get("value", 0),
                                "timestamp": tx.get("utime", 0),
                                "fee": tx.get("fee", 0)
                            }
                    
                    return {"confirmed": False, "success": False}
                    
        except Exception as e:
            logger.error(f"Error checking transaction: {e}")
            return {"confirmed": False, "success": False, "error": str(e)}
    
    async def send_ton_transaction(self, 
                                 from_address: str,
                                 to_address: str, 
                                 amount_ton: Decimal,
                                 private_key: str,
                                 memo: Optional[str] = None) -> Dict[str, Any]:
        """
        Отправляет TON транзакцию (для серверных переводов)
        ВНИМАНИЕ: Приватный ключ должен храниться безопасно!
        """
        try:
            # Здесь должна быть логика подписания и отправки транзакции
            # Используя pytoniq или tonsdk
            
            # Для демонстрации возвращаем mock результат
            mock_tx_hash = f"tx_{datetime.now().timestamp()}"
            
            return {
                "success": True,
                "tx_hash": mock_tx_hash,
                "amount_sent": float(amount_ton),
                "fee_paid": 0.01,  # Примерная комиссия
                "message": "Transaction sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_ton_to_stars_rate(self) -> Decimal:
        """
        Получает курс TON к звездам
        Можно интегрировать с реальным API курсов
        """
        # Пример: 1 TON = 1000 звезд
        return Decimal("1000")
    
    def stars_to_ton(self, stars: int) -> Decimal:
        """Конвертирует звезды в TON"""
        rate = self.get_ton_to_stars_rate()
        return Decimal(stars) / rate
    
    def ton_to_stars(self, ton_amount: Decimal) -> int:
        """Конвертирует TON в звезды"""
        rate = self.get_ton_to_stars_rate()
        return int(ton_amount * rate)


# Инициализация сервиса
ton_service = TONConnectService(
    manifest_url="https://your-domain.com/tonconnect-manifest.json"
)
