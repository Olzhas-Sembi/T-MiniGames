"""
API endpoints для платежной системы и NFT
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

from server.database_sqlite import get_db, User, Transaction, NFTItem as DBNFTItem, UserNFT as DBUserNFT, Case as DBCase, CaseItem, RouletteDraw
from server.models_nft import (
    PaymentRequest, TONConnectRequest, TelegramStarsRequest, 
    NFTListResponse, PaymentResponse, CaseOpenResult, NFTItem, UserNFT
)
from server.services.ton_service import ton_service
from server.services.telegram_stars_service import TelegramStarsService
from server.services.nft_service import nft_service
from server.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])
nft_router = APIRouter(prefix="/api/nft", tags=["nft"])

# Инициализация сервисов
stars_service = TelegramStarsService(bot_token=settings.TELEGRAM_BOT_TOKEN)

@router.post("/stars/create-invoice")
async def create_stars_invoice(
    request: TelegramStarsRequest,
    db: Session = Depends(get_db)
):
    """Создает инвойс для оплаты Telegram Stars"""
    try:
        # Проверяем пользователя
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Генерируем payload
        payload = stars_service.generate_stars_payload(
            user_id=request.user_id,
            transaction_type="stars_purchase",
            amount=request.amount_stars
        )
        
        # Создаем транзакцию в БД
        transaction = Transaction(
            user_id=request.user_id,
            type="stars_purchase",
            amount=request.amount_stars,
            payment_method="telegram_stars",
            status="pending",
            description=f"Purchase {request.amount_stars} stars"
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Создаем инвойс
        if hasattr(user, 'telegram_id') and user.telegram_id:
            # Если у нас есть chat_id, создаем инвойс для чата
            result = await stars_service.create_star_invoice(
                chat_id=int(user.telegram_id),
                title=request.invoice_title,
                description=request.invoice_description,
                stars_amount=request.amount_stars,
                payload=f"{transaction.id}:{payload}"
            )
        else:
            # Иначе создаем универсальную ссылку
            result = await stars_service.create_star_link(
                title=request.invoice_title,
                description=request.invoice_description,
                stars_amount=request.amount_stars,
                payload=f"{transaction.id}:{payload}"
            )
        
        if result["success"]:
            return PaymentResponse(
                success=True,
                transaction_id=transaction.id,
                payment_url=result.get("invoice_link", result.get("invoice_url")),
                message="Invoice created successfully"
            )
        else:
            # Отменяем транзакцию при ошибке
            transaction.status = "failed"
            db.commit()
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error creating stars invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ton/create-payment")
async def create_ton_payment(
    request: TONConnectRequest,
    db: Session = Depends(get_db)
):
    """Создает платеж TON Connect"""
    try:
        # Проверяем пользователя
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Конвертируем TON в звезды для записи в БД
        stars_equivalent = ton_service.ton_to_stars(request.amount_ton)
        
        # Создаем транзакцию в БД
        transaction = Transaction(
            user_id=request.user_id,
            type="ton_deposit",
            amount=stars_equivalent,
            payment_method="ton_connect",
            status="pending",
            description=f"TON deposit {request.amount_ton} TON"
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Генерируем платежную ссылку
        payment_link = await ton_service.generate_payment_link(
            recipient_address=request.destination_address,
            amount_ton=request.amount_ton,
            memo=f"deposit_{transaction.id}"
        )
        
        return PaymentResponse(
            success=True,
            transaction_id=transaction.id,
            payment_url=payment_link["universal_link"],
            qr_code=payment_link["qr_code"],
            message="TON payment link created"
        )
        
    except Exception as e:
        logger.error(f"Error creating TON payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/stars")
async def stars_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Webhook для обработки Telegram Stars платежей"""
    try:
        body = await request.body()
        
        # Проверяем подпись (если настроена)
        signature = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not stars_service.verify_webhook_signature(body, signature):
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        data = json.loads(body.decode())
        
        # Обрабатываем платеж
        payment_result = await stars_service.handle_successful_payment(data)
        
        if payment_result["type"] == "pre_checkout":
            # Отвечаем на предварительную проверку
            await stars_service.answer_pre_checkout_query(
                query_id=payment_result["query_id"],
                ok=payment_result["should_approve"]
            )
            
        elif payment_result["type"] == "successful_payment":
            # Обрабатываем успешный платеж в фоне
            background_tasks.add_task(
                process_successful_stars_payment,
                payment_result,
                db
            )
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error processing stars webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_successful_stars_payment(payment_data: Dict[str, Any], db: Session):
    """Обрабатывает успешный Stars платеж в фоне"""
    try:
        # Извлекаем transaction_id из payload
        payload = payment_data["payload"]
        transaction_id = payload.split(":")[0]
        
        # Находим транзакцию
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found")
            return
        
        # Обновляем статус транзакции
        transaction.status = "success"
        transaction.telegram_payment_id = payment_data["payment_id"]
        transaction.updated_at = datetime.now()
        
        # Начисляем звезды пользователю
        user = db.query(User).filter(User.id == transaction.user_id).first()
        if user:
            user.stars_balance += transaction.amount
            
        db.commit()
        logger.info(f"Stars payment processed: {transaction.amount} stars to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error processing stars payment: {e}")

@router.post("/webhook/ton")
async def ton_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Webhook для обработки TON платежей"""
    try:
        data = await request.json()
        
        # Здесь должна быть логика обработки TON webhook'ов
        # В зависимости от используемого провайдера (TonAPI, TonCenter и т.д.)
        
        tx_hash = data.get("tx_hash")
        amount_ton = data.get("amount")
        memo = data.get("memo", "")
        
        if "deposit_" in memo:
            transaction_id = memo.replace("deposit_", "")
            
            # Находим транзакцию
            transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
            if transaction:
                # Проверяем статус транзакции в блокчейне
                tx_status = await ton_service.check_transaction_status(tx_hash)
                
                if tx_status["confirmed"] and tx_status["success"]:
                    # Обновляем транзакцию
                    transaction.status = "success"
                    transaction.ton_transaction_hash = tx_hash
                    transaction.updated_at = datetime.now()
                    
                    # Начисляем звезды
                    user = db.query(User).filter(User.id == transaction.user_id).first()
                    if user:
                        user.stars_balance += transaction.amount
                    
                    db.commit()
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error processing TON webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# NFT Endpoints

@nft_router.get("/user/{user_id}/collection")
async def get_user_nft_collection(
    user_id: str,
    db: Session = Depends(get_db)
) -> NFTListResponse:
    """Получает коллекцию NFT пользователя"""
    try:
        # Получаем NFT пользователя
        user_nfts = db.query(DBUserNFT).filter(DBUserNFT.user_id == user_id).all()
        
        # Подсчитываем общую стоимость
        total_value_stars = 0
        total_value_ton = 0.0
        
        for user_nft in user_nfts:
            nft_item = db.query(DBNFTItem).filter(DBNFTItem.id == user_nft.nft_item_id).first()
            if nft_item:
                total_value_stars += nft_item.stars_value
                if nft_item.ton_value:
                    total_value_ton += float(nft_item.ton_value)
        
        return NFTListResponse(
            nfts=[UserNFT(
                id=nft.id,
                user_id=nft.user_id,
                nft_item_id=nft.nft_item_id,
                acquired_at=nft.acquired_at,
                acquired_from=nft.acquired_from,
                is_equipped=nft.is_equipped
            ) for nft in user_nfts],
            total_value_stars=total_value_stars,
            total_value_ton=total_value_ton
        )
        
    except Exception as e:
        logger.error(f"Error getting user NFT collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@nft_router.get("/cases")
async def get_available_cases(db: Session = Depends(get_db)):
    """Получает доступные кейсы"""
    try:
        cases = db.query(DBCase).filter(DBCase.is_active == True).all()
        return [
            {
                "id": case.id,
                "name": case.name,
                "description": case.description,
                "image_url": case.image_url,
                "price_stars": case.price_stars,
                "price_ton": float(case.price_ton) if case.price_ton else None
            }
            for case in cases
        ]
        
    except Exception as e:
        logger.error(f"Error getting cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@nft_router.post("/cases/{case_id}/open")
async def open_case(
    case_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Открывает кейс и выдает NFT"""
    try:
        # Проверяем пользователя и кейс
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        case = db.query(DBCase).filter(DBCase.id == case_id, DBCase.is_active == True).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Проверяем баланс пользователя
        if user.stars_balance < case.price_stars:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Получаем предметы в кейсе
        case_items = db.query(CaseItem).filter(CaseItem.case_id == case_id).all()
        if not case_items:
            raise HTTPException(status_code=400, detail="Case has no items")
        
        # Списываем стоимость кейса
        user.stars_balance -= case.price_stars
        
        # Определяем выпавший предмет (упрощенная логика)
        import random
        total_chance = sum(float(item.drop_chance) for item in case_items)
        random_value = random.random() * total_chance
        
        current_chance = 0.0
        selected_item = None
        for item in case_items:
            current_chance += float(item.drop_chance)
            if random_value <= current_chance:
                selected_item = item
                break
        
        if not selected_item:
            selected_item = case_items[0]  # Fallback
        
        # Получаем информацию о NFT предмете
        nft_item = db.query(DBNFTItem).filter(DBNFTItem.id == selected_item.nft_item_id).first()
        if not nft_item:
            raise HTTPException(status_code=400, detail="NFT item not found")
        
        # Создаем экземпляр NFT для пользователя
        user_nft = DBUserNFT(
            user_id=user_id,
            nft_item_id=nft_item.id,
            acquired_from="case_opening",
            is_equipped=False
        )
        db.add(user_nft)
        
        # Создаем транзакцию списания через прямой SQL (только с существующими полями)
        import uuid
        from sqlalchemy import text
        transaction_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO transactions (id, user_id, type, amount, description, room_id, created_at)
            VALUES (:transaction_id, :user_id, 'case_purchase', :amount, :description, NULL, datetime('now'))
        """), {
            'transaction_id': transaction_id,
            'user_id': user_id,
            'amount': -case.price_stars,
            'description': f'Opened case: {case.name}'
        })
        
        db.commit()
        
        return {
            "success": True,
            "nft_item": {
                "id": nft_item.id,
                "name": nft_item.name,
                "description": nft_item.description,
                "image_url": nft_item.image_url,
                "rarity": nft_item.rarity,
                "nft_type": nft_item.nft_type,
                "stars_value": float(nft_item.stars_value)
            },
            "total_value": float(nft_item.stars_value),
            "user_nft_id": user_nft.id,
            "remaining_balance": user.stars_balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error opening case: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@nft_router.get("/balance/{user_id}")
async def get_payment_balance(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Получает баланс пользователя"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user_id,
            "stars_balance": user.stars_balance,
            "ton_equivalent": float(ton_service.stars_to_ton(user.stars_balance)),
            "last_updated": user.updated_at
        }
        
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rates")
async def get_exchange_rates():
    """Получает текущие курсы обмена"""
    try:
        ton_to_stars_rate = ton_service.get_ton_to_stars_rate()
        
        return {
            "ton_to_stars": float(ton_to_stars_rate),
            "stars_to_ton": float(1 / ton_to_stars_rate),
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
