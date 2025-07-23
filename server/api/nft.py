from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from ..database_sqlite import get_db, User, NFTItem, UserNFT, Case, RouletteDraw, Transaction
from ..models_nft import NFTItemResponse, UserNFTResponse, CaseResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/nft", tags=["nft"])

@router.get("/cases", response_model=List[CaseResponse])
async def get_available_cases(db: Session = Depends(get_db)):
    """Получить список доступных кейсов"""
    try:
        cases = db.query(Case).filter(Case.is_active == True).all()
        return [CaseResponse.from_orm(case) for case in cases]
    except Exception as e:
        logger.error(f"Error fetching cases: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user/{user_id}/collection")
async def get_user_nft_collection(
    user_id: str,
    nft_type: Optional[str] = None,
    rarity: Optional[str] = None,
    equipped_only: bool = False,
    db: Session = Depends(get_db)
):
    """Получить NFT коллекцию пользователя"""
    try:
        # Проверяем существование пользователя
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Формируем запрос с джойном к NFTItem
        query = db.query(UserNFT).join(NFTItem).filter(UserNFT.user_id == user.id)
        
        # Применяем фильтры
        if nft_type:
            query = query.filter(NFTItem.nft_type == nft_type)
        if rarity:
            query = query.filter(NFTItem.rarity == rarity)
        if equipped_only:
            query = query.filter(UserNFT.is_equipped == True)
        
        # Загружаем данные с включением NFTItem
        user_nfts = query.options(joinedload(UserNFT.nft_item)).all()
        
        # Формируем ответ
        nfts = []
        for user_nft in user_nfts:
            nft_data = {
                "id": user_nft.id,
                "user_id": str(user_nft.user_id),
                "nft_item_id": user_nft.nft_item_id,
                "acquired_at": user_nft.acquired_at.isoformat(),
                "acquired_from": user_nft.acquired_from,
                "is_equipped": user_nft.is_equipped,
                "nft_item": {
                    "id": user_nft.nft_item.id,
                    "name": user_nft.nft_item.name,
                    "description": user_nft.nft_item.description,
                    "image_url": user_nft.nft_item.image_url,
                    "rarity": user_nft.nft_item.rarity,
                    "nft_type": user_nft.nft_item.nft_type,
                    "stars_value": user_nft.nft_item.stars_value
                }
            }
            nfts.append(nft_data)
        
        # Статистика коллекции
        total_value = sum(nft["nft_item"]["stars_value"] for nft in nfts)
        equipped_count = len([nft for nft in nfts if nft["is_equipped"]])
        
        rarity_counts = {}
        for nft in nfts:
            rarity = nft["nft_item"]["rarity"]
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        return {
            "nfts": nfts,
            "stats": {
                "total_count": len(nfts),
                "total_value": total_value,
                "equipped_count": equipped_count,
                "rarity_distribution": rarity_counts
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user NFT collection: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/user/{user_id}/equip/{nft_id}")
async def equip_nft(
    user_id: str,
    nft_id: str,
    db: Session = Depends(get_db)
):
    """Экипировать NFT"""
    try:
        # Находим пользователя
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Находим NFT пользователя
        user_nft = db.query(UserNFT).filter(
            UserNFT.id == nft_id,
            UserNFT.user_id == user.id
        ).first()
        
        if not user_nft:
            raise HTTPException(status_code=404, detail="NFT not found")
        
        # Снимаем экипировку с других NFT того же типа
        db.query(UserNFT).join(NFTItem).filter(
            UserNFT.user_id == user.id,
            NFTItem.nft_type == user_nft.nft_item.nft_type,
            UserNFT.id != nft_id
        ).update({"is_equipped": False})
        
        # Экипируем выбранный NFT
        user_nft.is_equipped = True
        db.commit()
        
        return {"message": "NFT equipped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error equipping NFT: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/user/{user_id}/unequip/{nft_id}")
async def unequip_nft(
    user_id: str,
    nft_id: str,
    db: Session = Depends(get_db)
):
    """Снять экипировку NFT"""
    try:
        # Находим пользователя
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Находим NFT пользователя
        user_nft = db.query(UserNFT).filter(
            UserNFT.id == nft_id,
            UserNFT.user_id == user.id
        ).first()
        
        if not user_nft:
            raise HTTPException(status_code=404, detail="NFT not found")
        
        # Снимаем экипировку
        user_nft.is_equipped = False
        db.commit()
        
        return {"message": "NFT unequipped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unequipping NFT: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user/{user_id}/equipped")
async def get_equipped_nfts(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Получить экипированные NFT пользователя"""
    try:
        # Находим пользователя
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем экипированные NFT
        equipped_nfts = db.query(UserNFT).join(NFTItem).filter(
            UserNFT.user_id == user.id,
            UserNFT.is_equipped == True
        ).options(joinedload(UserNFT.nft_item)).all()
        
        # Группируем по типу NFT
        equipped_by_type = {}
        for user_nft in equipped_nfts:
            nft_type = user_nft.nft_item.nft_type
            equipped_by_type[nft_type] = {
                "id": user_nft.id,
                "nft_item": {
                    "id": user_nft.nft_item.id,
                    "name": user_nft.nft_item.name,
                    "description": user_nft.nft_item.description,
                    "image_url": user_nft.nft_item.image_url,
                    "rarity": user_nft.nft_item.rarity,
                    "nft_type": user_nft.nft_item.nft_type,
                    "stars_value": user_nft.nft_item.stars_value
                }
            }
        
        return {"equipped_nfts": equipped_by_type}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching equipped NFTs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/marketplace")
async def get_marketplace_nfts(
    nft_type: Optional[str] = None,
    rarity: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Получить NFT доступные в маркетплейсе (пока заглушка)"""
    try:
        # Пока возвращаем все NFT предметы как доступные
        query = db.query(NFTItem)
        
        if nft_type:
            query = query.filter(NFTItem.nft_type == nft_type)
        if rarity:
            query = query.filter(NFTItem.rarity == rarity)
        if min_price:
            query = query.filter(NFTItem.stars_value >= min_price)
        if max_price:
            query = query.filter(NFTItem.stars_value <= max_price)
        
        nft_items = query.offset(offset).limit(limit).all()
        
        return {
            "nfts": [NFTItemResponse.from_orm(item) for item in nft_items],
            "total": query.count()
        }
        
    except Exception as e:
        logger.error(f"Error fetching marketplace NFTs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user/{user_id}/history")
async def get_user_nft_history(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Получить историю NFT операций пользователя"""
    try:
        # Находим пользователя
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем историю рулетки (открытия кейсов)
        roulette_history = db.query(RouletteDraw).filter(
            RouletteDraw.user_id == user.id
        ).order_by(RouletteDraw.created_at.desc()).offset(offset).limit(limit).all()
        
        history = []
        for draw in roulette_history:
            history.append({
                "id": draw.id,
                "type": "case_opening",
                "case_name": draw.case_name,
                "won_nft_name": draw.won_nft_name,
                "won_nft_rarity": draw.won_nft_rarity,
                "total_value": draw.total_value,
                "created_at": draw.created_at.isoformat()
            })
        
        return {
            "history": history,
            "total": db.query(RouletteDraw).filter(RouletteDraw.user_id == user.id).count()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user NFT history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
