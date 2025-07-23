"""
NFT Management Service для Telegram Mini Games
Обеспечивает:
- Создание и управление NFT
- Логику кейсов и розыгрышей 
- Трансферы и торговлю
- Генерацию изображений NFT
"""

import random
import json
import hashlib
import secrets
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import logging

from server.models_nft import (
    NFTItem, NFTRarity, NFTType, UserNFT, Case, CaseItem, 
    RouletteDraw, RouletteParticipation, CaseOpenResult
)

logger = logging.getLogger(__name__)

class NFTService:
    """Сервис для управления NFT системой"""
    
    def __init__(self):
        # Таблица редкостей и их вероятностей
        self.rarity_chances = {
            NFTRarity.COMMON: 0.60,      # 60%
            NFTRarity.UNCOMMON: 0.25,    # 25%
            NFTRarity.RARE: 0.10,        # 10%
            NFTRarity.EPIC: 0.04,        # 4%
            NFTRarity.LEGENDARY: 0.01    # 1%
        }
        
        # Множители стоимости по редкости
        self.rarity_multipliers = {
            NFTRarity.COMMON: 1.0,
            NFTRarity.UNCOMMON: 2.5,
            NFTRarity.RARE: 5.0,
            NFTRarity.EPIC: 10.0,
            NFTRarity.LEGENDARY: 25.0
        }
        
        # Базовые цвета для редкостей
        self.rarity_colors = {
            NFTRarity.COMMON: "#A8A8A8",      # Серый
            NFTRarity.UNCOMMON: "#4CAF50",    # Зеленый
            NFTRarity.RARE: "#2196F3",        # Синий
            NFTRarity.EPIC: "#9C27B0",        # Фиолетовый
            NFTRarity.LEGENDARY: "#FF9800"    # Оранжевый
        }
    
    def generate_nft_seed(self, user_id: str, case_id: str, timestamp: Optional[datetime] = None) -> str:
        """
        Генерирует криптографический seed для честного выпадения NFT
        """
        if not timestamp:
            timestamp = datetime.now()
            
        seed_data = f"{user_id}:{case_id}:{timestamp.isoformat()}:{secrets.token_hex(16)}"
        return hashlib.sha256(seed_data.encode()).hexdigest()
    
    def determine_nft_rarity(self, seed: str, boost_multiplier: float = 1.0) -> NFTRarity:
        """
        Определяет редкость NFT на основе seed
        boost_multiplier - множитель для увеличения шансов редких предметов
        """
        # Используем seed для генерации детерминированного числа
        hash_int = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
        random_value = (hash_int % 10000) / 10000.0  # 0.0 - 1.0
        
        # Применяем буст (сдвигаем вероятности в пользу редких)
        if boost_multiplier > 1.0:
            random_value = random_value ** (1.0 / boost_multiplier)
        
        # Определяем редкость по накопительным вероятностям
        cumulative = 0.0
        for rarity, chance in self.rarity_chances.items():
            cumulative += chance
            if random_value <= cumulative:
                return rarity
        
        return NFTRarity.COMMON  # Fallback
    
    def calculate_nft_value(self, base_value: int, rarity: NFTRarity) -> int:
        """
        Рассчитывает стоимость NFT с учетом редкости
        """
        multiplier = self.rarity_multipliers[rarity]
        return int(base_value * multiplier)
    
    async def open_case(self, case: Case, user_id: str) -> CaseOpenResult:
        """
        Открывает кейс и возвращает выпавший NFT
        """
        try:
            # Генерируем seed для честности
            seed = self.generate_nft_seed(user_id, case.id)
            
            # Определяем какой предмет выпадет
            total_chance = sum(item.drop_chance for item in case.items)
            
            # Генерируем число для выбора предмета
            hash_int = int(hashlib.md5(f"{seed}_item".encode()).hexdigest()[:8], 16)
            item_random = (hash_int % 10000) / 10000.0 * total_chance
            
            # Выбираем предмет
            cumulative = 0.0
            selected_item = None
            
            for case_item in case.items:
                cumulative += case_item.drop_chance
                if item_random <= cumulative:
                    selected_item = case_item
                    break
            
            if not selected_item:
                selected_item = case.items[0]  # Fallback
            
            # Определяем итоговую редкость (может отличаться от базовой)
            final_rarity = self.determine_nft_rarity(f"{seed}_rarity")
            
            # Рассчитываем итоговую стоимость
            base_value = random.randint(selected_item.min_value, selected_item.max_value)
            final_value = self.calculate_nft_value(base_value, final_rarity)
            
            # Создаем NFT для пользователя
            user_nft = UserNFT(
                user_id=user_id,
                nft_item_id=selected_item.nft_item_id,
                acquired_from="case_battle"
            )
            
            # Получаем данные NFT предмета (в реальном приложении из БД)
            nft_item = NFTItem(
                id=selected_item.nft_item_id,
                name=f"Case Drop #{secrets.token_hex(4)}",
                description=f"Dropped from {case.name}",
                image_url=self.generate_nft_image_url(final_rarity),
                rarity=final_rarity,
                nft_type=NFTType.COLLECTIBLE,
                stars_value=final_value
            )
            
            return CaseOpenResult(
                nft_item=nft_item,
                user_nft_id=user_nft.id,
                rarity_multiplier=self.rarity_multipliers[final_rarity],
                total_value=final_value
            )
            
        except Exception as e:
            logger.error(f"Error opening case: {e}")
            raise
    
    def generate_nft_image_url(self, rarity: NFTRarity) -> str:
        """
        Генерирует URL изображения NFT или создает простое изображение
        """
        try:
            # Создаем простое изображение NFT
            img = Image.new('RGB', (512, 512), color=self.rarity_colors[rarity])
            draw = ImageDraw.Draw(img)
            
            # Добавляем текст с редкостью
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            text = rarity.value.upper()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (512 - text_width) // 2
            y = (512 - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font)
            
            # Конвертируем в base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Error generating NFT image: {e}")
            # Возвращаем placeholder
            return f"https://via.placeholder.com/512x512/{self.rarity_colors[rarity][1:]}/FFFFFF?text={rarity.value}"
    
    async def participate_in_roulette(self, 
                                    draw: RouletteDraw, 
                                    user_id: str, 
                                    bet_amount: int) -> RouletteParticipation:
        """
        Добавляет участника в розыгрыш рулетки
        """
        try:
            participation = RouletteParticipation(
                draw_id=draw.id,
                user_id=user_id,
                amount_bet=bet_amount
            )
            
            return participation
            
        except Exception as e:
            logger.error(f"Error participating in roulette: {e}")
            raise
    
    def determine_roulette_winner(self, 
                                participations: List[RouletteParticipation],
                                seed: Optional[str] = None) -> str:
        """
        Определяет победителя розыгрыша рулетки пропорционально ставкам
        """
        try:
            if not participations:
                raise ValueError("No participants")
            
            if not seed:
                seed = secrets.token_hex(32)
            
            # Создаем взвешенный список участников
            weighted_participants = []
            for participation in participations:
                # Добавляем участника количество раз пропорционально его ставке
                for _ in range(participation.amount_bet):
                    weighted_participants.append(participation.user_id)
            
            # Используем seed для детерминированного выбора
            hash_int = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
            winner_index = hash_int % len(weighted_participants)
            
            return weighted_participants[winner_index]
            
        except Exception as e:
            logger.error(f"Error determining roulette winner: {e}")
            raise
    
    def get_user_nft_stats(self, user_nfts: List[UserNFT]) -> Dict[str, Any]:
        """
        Подсчитывает статистику NFT пользователя
        """
        try:
            stats = {
                "total_nfts": len(user_nfts),
                "by_rarity": {rarity.value: 0 for rarity in NFTRarity},
                "by_type": {nft_type.value: 0 for nft_type in NFTType},
                "total_value_stars": 0,
                "equipped_count": 0
            }
            
            for user_nft in user_nfts:
                # В реальном приложении нужно подгружать nft_item из БД
                # stats["by_rarity"][user_nft.nft_item.rarity] += 1
                # stats["by_type"][user_nft.nft_item.nft_type] += 1
                # stats["total_value_stars"] += user_nft.nft_item.stars_value
                
                if user_nft.is_equipped:
                    stats["equipped_count"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating NFT stats: {e}")
            return {"error": str(e)}
    
    def create_default_nft_collection(self) -> List[NFTItem]:
        """
        Создает базовую коллекцию NFT для начала
        """
        nfts = []
        
        # Аватары
        for rarity in NFTRarity:
            nft = NFTItem(
                name=f"{rarity.value.title()} Avatar",
                description=f"A {rarity.value} avatar for your profile",
                image_url=self.generate_nft_image_url(rarity),
                rarity=rarity,
                nft_type=NFTType.AVATAR,
                stars_value=self.calculate_nft_value(100, rarity)
            )
            nfts.append(nft)
        
        # Карточки
        for rarity in [NFTRarity.UNCOMMON, NFTRarity.RARE, NFTRarity.EPIC]:
            nft = NFTItem(
                name=f"{rarity.value.title()} Card",
                description=f"A collectible {rarity.value} game card",
                image_url=self.generate_nft_image_url(rarity),
                rarity=rarity,
                nft_type=NFTType.CARD,
                stars_value=self.calculate_nft_value(50, rarity)
            )
            nfts.append(nft)
        
        # Рамки
        for rarity in [NFTRarity.RARE, NFTRarity.EPIC, NFTRarity.LEGENDARY]:
            nft = NFTItem(
                name=f"{rarity.value.title()} Frame",
                description=f"A premium {rarity.value} profile frame",
                image_url=self.generate_nft_image_url(rarity),
                rarity=rarity,
                nft_type=NFTType.FRAME,
                stars_value=self.calculate_nft_value(200, rarity)
            )
            nfts.append(nft)
        
        return nfts
    
    def create_default_cases(self, nft_items: List[NFTItem]) -> List[Case]:
        """
        Создает базовые кейсы для открытия
        """
        cases = []
        
        # Обычный кейс
        common_case = Case(
            name="Starter Case",
            description="A basic case with common to rare items",
            image_url="https://via.placeholder.com/256x256/4CAF50/FFFFFF?text=STARTER",
            price_stars=100
        )
        
        # Добавляем предметы в кейс
        common_case.items = [
            CaseItem(
                case_id=common_case.id,
                nft_item_id=nft.id,
                drop_chance=0.4 if nft.rarity == NFTRarity.COMMON else
                           0.3 if nft.rarity == NFTRarity.UNCOMMON else
                           0.2 if nft.rarity == NFTRarity.RARE else 0.1,
                min_value=nft.stars_value,
                max_value=int(nft.stars_value * 1.5)
            )
            for nft in nft_items[:10]  # Первые 10 NFT
        ]
        
        cases.append(common_case)
        
        # Премиум кейс
        premium_case = Case(
            name="Premium Case",
            description="High-value case with rare to legendary items",
            image_url="https://via.placeholder.com/256x256/FF9800/FFFFFF?text=PREMIUM",
            price_stars=500
        )
        
        premium_case.items = [
            CaseItem(
                case_id=premium_case.id,
                nft_item_id=nft.id,
                drop_chance=0.4 if nft.rarity == NFTRarity.RARE else
                           0.35 if nft.rarity == NFTRarity.EPIC else
                           0.25 if nft.rarity == NFTRarity.LEGENDARY else 0.0,
                min_value=nft.stars_value,
                max_value=int(nft.stars_value * 2.0)
            )
            for nft in nft_items if nft.rarity in [NFTRarity.RARE, NFTRarity.EPIC, NFTRarity.LEGENDARY]
        ]
        
        cases.append(premium_case)
        
        return cases


# Инициализация сервиса
nft_service = NFTService()
