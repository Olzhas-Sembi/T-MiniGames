"""
Telegram Stars интеграция для платежей
Обеспечивает:
- Создание инвойсов Telegram Stars
- Обработку webhook'ов платежей
- Рефанды и возвраты
"""

import json
import hashlib
import hmac
import aiohttp
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TelegramStarsService:
    """Сервис для работы с Telegram Stars платежами"""
    
    def __init__(self, bot_token: str, webhook_secret: Optional[str] = None):
        self.bot_token = bot_token
        self.webhook_secret = webhook_secret
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
    
    async def create_star_invoice(self, 
                                chat_id: int,
                                title: str, 
                                description: str,
                                stars_amount: int,
                                payload: str,
                                photo_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Создает инвойс для оплаты Telegram Stars
        """
        try:
            # Параметры инвойса
            invoice_params = {
                "chat_id": chat_id,
                "title": title,
                "description": description,
                "payload": payload,
                "currency": "XTR",  # Код валюты для Stars
                "prices": [{"label": "Stars", "amount": stars_amount}],
                "start_parameter": f"stars_{payload}",
            }
            
            if photo_url:
                invoice_params["photo_url"] = photo_url
                invoice_params["photo_width"] = 512
                invoice_params["photo_height"] = 512
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/sendInvoice"
                
                async with session.post(url, json=invoice_params) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        return {
                            "success": True,
                            "message_id": data["result"]["message_id"],
                            "invoice_url": f"https://t.me/invoice/{payload}",
                            "payload": payload
                        }
                    else:
                        logger.error(f"Failed to create invoice: {data}")
                        return {
                            "success": False,
                            "error": data.get("description", "Unknown error")
                        }
                        
        except Exception as e:
            logger.error(f"Error creating star invoice: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_star_link(self,
                             title: str,
                             description: str, 
                             stars_amount: int,
                             payload: str,
                             photo_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Создает ссылку для оплаты Stars (без привязки к чату)
        """
        try:
            link_params = {
                "title": title,
                "description": description,
                "payload": payload,
                "currency": "XTR",
                "prices": [{"label": "Stars", "amount": stars_amount}],
            }
            
            if photo_url:
                link_params["photo_url"] = photo_url
                link_params["photo_width"] = 512
                link_params["photo_height"] = 512
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/createInvoiceLink"
                
                async with session.post(url, json=link_params) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        return {
                            "success": True,
                            "invoice_link": data["result"],
                            "payload": payload,
                            "stars_amount": stars_amount
                        }
                    else:
                        logger.error(f"Failed to create invoice link: {data}")
                        return {
                            "success": False,
                            "error": data.get("description", "Unknown error")
                        }
                        
        except Exception as e:
            logger.error(f"Error creating star link: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """
        Проверяет подпись webhook'а от Telegram
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return True  # Разрешаем, если секрет не настроен
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def handle_successful_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает успешный платеж Stars
        """
        try:
            # Извлекаем данные платежа
            pre_checkout_query = payment_data.get("pre_checkout_query")
            successful_payment = payment_data.get("successful_payment")
            
            if pre_checkout_query:
                # Это запрос на предварительную проверку
                query_id = pre_checkout_query["id"]
                payload = pre_checkout_query["invoice_payload"]
                stars_amount = pre_checkout_query["total_amount"]
                
                # Здесь можно добавить дополнительные проверки
                # Например, проверить достаточность товара на складе
                
                return {
                    "type": "pre_checkout",
                    "query_id": query_id,
                    "payload": payload,
                    "stars_amount": stars_amount,
                    "should_approve": True
                }
                
            elif successful_payment:
                # Это подтверждение успешного платежа
                payload = successful_payment["invoice_payload"]
                stars_amount = successful_payment["total_amount"]
                telegram_payment_charge_id = successful_payment["telegram_payment_charge_id"]
                
                return {
                    "type": "successful_payment",
                    "payload": payload,
                    "stars_amount": stars_amount,
                    "payment_id": telegram_payment_charge_id,
                    "timestamp": datetime.now()
                }
            
            return {"type": "unknown", "data": payment_data}
            
        except Exception as e:
            logger.error(f"Error handling payment: {e}")
            return {"type": "error", "error": str(e)}
    
    async def answer_pre_checkout_query(self, query_id: str, ok: bool, error_message: Optional[str] = None) -> bool:
        """
        Отвечает на pre-checkout query
        """
        try:
            params = {"pre_checkout_query_id": query_id, "ok": ok}
            if not ok and error_message:
                params["error_message"] = error_message
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/answerPreCheckoutQuery"
                
                async with session.post(url, json=params) as response:
                    data = await response.json()
                    return data.get("ok", False)
                    
        except Exception as e:
            logger.error(f"Error answering pre-checkout query: {e}")
            return False
    
    async def refund_star_payment(self, 
                                user_id: int,
                                telegram_payment_charge_id: str) -> Dict[str, Any]:
        """
        Возвращает Stars платеж
        """
        try:
            params = {
                "user_id": user_id,
                "telegram_payment_charge_id": telegram_payment_charge_id
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/refundStarPayment"
                
                async with session.post(url, json=params) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        return {
                            "success": True,
                            "refunded": True
                        }
                    else:
                        return {
                            "success": False,
                            "error": data.get("description", "Refund failed")
                        }
                        
        except Exception as e:
            logger.error(f"Error refunding payment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_stars_payload(self, user_id: str, transaction_type: str, amount: int) -> str:
        """
        Генерирует payload для Stars платежа
        """
        payload_data = {
            "user_id": user_id,
            "type": transaction_type,
            "amount": amount,
            "timestamp": int(datetime.now().timestamp())
        }
        
        return json.dumps(payload_data)
    
    def parse_stars_payload(self, payload: str) -> Dict[str, Any]:
        """
        Парсит payload от Stars платежа
        """
        try:
            return json.loads(payload)
        except Exception as e:
            logger.error(f"Error parsing payload: {e}")
            return {}
    
    async def get_star_transactions(self, offset: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает историю Star транзакций
        """
        try:
            params = {
                "offset": offset,
                "limit": limit
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/getStarTransactions"
                
                async with session.post(url, json=params) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        return data.get("result", {}).get("transactions", [])
                    else:
                        logger.error(f"Failed to get transactions: {data}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting star transactions: {e}")
            return []


# Инициализация сервиса (токен нужно будет передать из конфига)
# stars_service = TelegramStarsService(bot_token="YOUR_BOT_TOKEN")
