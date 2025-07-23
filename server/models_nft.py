"""
Модели для NFT системы и расширенных платежей
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class NFTRarity(str, Enum):
    """Редкость NFT"""
    COMMON = "common"
    UNCOMMON = "uncommon" 
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class NFTType(str, Enum):
    """Тип NFT"""
    AVATAR = "avatar"
    CARD = "card"
    STICKER = "sticker"
    FRAME = "frame"
    GIFT = "gift"
    COLLECTIBLE = "collectible"

class PaymentMethod(str, Enum):
    """Способы платежа"""
    TELEGRAM_STARS = "telegram_stars"
    TON_CONNECT = "ton_connect"
    INTERNAL_TRANSFER = "internal_transfer"

class TransactionStatus(str, Enum):
    """Статусы транзакций"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NFTItem(BaseModel):
    """Модель NFT предмета"""
    id: str = str(uuid.uuid4())
    name: str
    description: str
    image_url: str
    rarity: NFTRarity
    nft_type: NFTType
    stars_value: int  # Стоимость в звездах
    ton_value: Optional[float] = None  # Стоимость в TON

class NFTItemResponse(BaseModel):
    """Response модель для NFT предмета"""
    id: str
    name: str
    description: str
    image_url: str
    rarity: str
    nft_type: str
    stars_value: int
    ton_value: Optional[float] = None
    
    class Config:
        from_attributes = True
    metadata: Dict[str, Any] = {}
    is_tradeable: bool = True
    created_at: datetime = datetime.now()

class UserNFT(BaseModel):
    """NFT в инвентаре пользователя"""
    id: str = str(uuid.uuid4())
    user_id: str
    nft_item_id: str
    acquired_at: datetime = datetime.now()
    acquired_from: str  # "case_battle", "roulette", "purchase", "gift"
    is_equipped: bool = False

class UserNFTResponse(BaseModel):
    """Response модель для NFT пользователя"""
    id: str
    user_id: str
    nft_item_id: str
    acquired_at: str
    acquired_from: str
    is_equipped: bool
    nft_item: Optional[NFTItemResponse] = None
    
    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    """Запрос на платеж"""
    user_id: str
    amount: float
    currency: str  # "stars", "ton"
    method: PaymentMethod
    description: str
    metadata: Dict[str, Any] = {}

class TONConnectRequest(BaseModel):
    """Запрос TONConnect платежа"""
    user_id: str
    amount_ton: float
    destination_address: str
    memo: Optional[str] = None
    wallet_address: str

class TelegramStarsRequest(BaseModel):
    """Запрос Telegram Stars платежа"""
    user_id: str
    amount_stars: int
    invoice_title: str
    invoice_description: str
    payload: str

class NFTTransaction(BaseModel):
    """Транзакция с NFT"""
    id: str = str(uuid.uuid4())
    from_user_id: Optional[str] = None
    to_user_id: str
    nft_item_id: str
    transaction_type: str  # "mint", "transfer", "burn", "purchase"
    stars_cost: Optional[int] = None
    ton_cost: Optional[float] = None
    created_at: datetime = datetime.now()

class CaseItem(BaseModel):
    """Предмет в кейсе"""
    nft_item_id: str
    drop_chance: float  # Шанс выпадения (0.0 - 1.0)
    min_value: int
    max_value: int

class Case(BaseModel):
    """Кейс для Case Battle"""
    id: str = str(uuid.uuid4())
    name: str
    description: str
    image_url: str
    price_stars: int
    price_ton: Optional[float] = None
    items: List[CaseItem]
    is_active: bool = True
    created_at: datetime = datetime.now()

class CaseResponse(BaseModel):
    """Response модель для кейса"""
    id: str
    name: str
    description: str
    image_url: str
    price_stars: int
    price_ton: Optional[float] = None
    is_active: bool
    
    class Config:
        from_attributes = True

class RouletteDraw(BaseModel):
    """Розыгрыш рулетки"""
    id: str = str(uuid.uuid4())
    title: str
    description: str
    prize_nft_id: str
    target_amount: int  # Целевая сумма в звездах
    min_bet: int
    max_bet: int
    current_amount: int = 0
    participants: List[str] = []  # user_id участников
    is_active: bool = True
    created_at: datetime = datetime.now()
    finished_at: Optional[datetime] = None
    winner_id: Optional[str] = None

class RouletteParticipation(BaseModel):
    """Участие в розыгрыше"""
    id: str = str(uuid.uuid4())
    draw_id: str
    user_id: str
    amount_bet: int
    created_at: datetime = datetime.now()

# Ответы API
class NFTListResponse(BaseModel):
    """Список NFT пользователя"""
    nfts: List[UserNFT]
    total_value_stars: int
    total_value_ton: float

class PaymentResponse(BaseModel):
    """Ответ на платежный запрос"""
    success: bool
    transaction_id: str
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    message: str

class CaseOpenResult(BaseModel):
    """Результат открытия кейса"""
    nft_item: NFTItem
    user_nft_id: str
    rarity_multiplier: float
    total_value: int
