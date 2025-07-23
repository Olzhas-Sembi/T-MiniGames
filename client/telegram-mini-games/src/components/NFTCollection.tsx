import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Star, Package, Trophy, Sparkles, Eye, ShoppingCart } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { baseURL } from '../config';

interface NFTItem {
  id: string;
  name: string;
  description: string;
  image_url: string;
  rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  nft_type: 'avatar' | 'card' | 'sticker' | 'frame' | 'gift' | 'collectible';
  stars_value: number;
  is_equipped?: boolean;
}

interface UserNFT {
  id: string;
  user_id: string;
  nft_item_id: string;
  acquired_at: string;
  acquired_from: string;
  is_equipped: boolean;
  nft_item?: NFTItem;
}

interface Case {
  id: string;
  name: string;
  description: string;
  image_url: string;
  price_stars: number;
  price_ton?: number;
}

interface NFTCollectionProps {
  userId: string;
  userBalance: number;
  onBalanceUpdate: (newBalance: number) => void;
}

const NFTCollection: React.FC<NFTCollectionProps> = ({ 
  userId, 
  userBalance, 
  onBalanceUpdate 
}) => {
  const [nfts, setNFTs] = useState<UserNFT[]>([]);
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [openingCase, setOpeningCase] = useState<string | null>(null);
  const [lastDrop, setLastDrop] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState('collection');

  const rarityColors = {
    common: 'bg-gray-500',
    uncommon: 'bg-green-500',
    rare: 'bg-blue-500',
    epic: 'bg-purple-500',
    legendary: 'bg-orange-500'
  };

  const rarityLabels = {
    common: 'Обычный',
    uncommon: 'Необычный',
    rare: 'Редкий',
    epic: 'Эпический',
    legendary: 'Легендарный'
  };

  useEffect(() => {
    loadNFTCollection();
    loadAvailableCases();
  }, [userId]);

  const loadNFTCollection = async () => {
    try {
      const response = await fetch(`${baseURL}/api/nft/user/${userId}/collection`);
      const data = await response.json();
      setNFTs(data.nfts || []);
    } catch (error) {
      console.error('Error loading NFT collection:', error);
    }
  };

  const loadAvailableCases = async () => {
    try {
      const response = await fetch(`${baseURL}/api/nft/cases`);
      const data = await response.json();
      setCases(data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading cases:', error);
      setLoading(false);
    }
  };

  const openCase = async (caseId: string, casePrice: number) => {
    if (userBalance < casePrice) {
      alert('Недостаточно звезд для открытия кейса!');
      return;
    }

    setOpeningCase(caseId);
    
    try {
      const response = await fetch(`${baseURL}/api/nft/cases/${caseId}/open`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId
        }),
      });

      const result = await response.json();
      
      if (response.ok) {
        setLastDrop(result);
        onBalanceUpdate(userBalance - casePrice);
        
        // Обновляем коллекцию
        await loadNFTCollection();
        
        // Показываем анимацию выпадения
        setTimeout(() => {
          setOpeningCase(null);
        }, 3000);
      } else {
        throw new Error(result.detail || 'Failed to open case');
      }
    } catch (error) {
      console.error('Error opening case:', error);
      alert('Ошибка при открытии кейса!');
      setOpeningCase(null);
    }
  };

  const NFTCard: React.FC<{ nft: UserNFT & { nft_item?: NFTItem } }> = ({ nft }) => (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.05 }}
      className="relative"
    >
      <Card className="overflow-hidden hover:shadow-lg transition-shadow">
        <div className="aspect-square relative">
          <img
            src={nft.nft_item?.image_url || '/placeholder-nft.png'}
            alt={nft.nft_item?.name}
            className="w-full h-full object-cover"
          />
          
          {/* Рамка редкости */}
          <div className={`absolute inset-0 border-4 ${rarityColors[nft.nft_item?.rarity || 'common']} opacity-60`} />
          
          {/* Бейдж редкости */}
          <Badge 
            className={`absolute top-2 right-2 ${rarityColors[nft.nft_item?.rarity || 'common']} text-white`}
          >
            {rarityLabels[nft.nft_item?.rarity || 'common']}
          </Badge>
          
          {/* Индикатор экипировки */}
          {nft.is_equipped && (
            <div className="absolute top-2 left-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
              <Eye className="w-3 h-3 text-white" />
            </div>
          )}
        </div>
        
        <CardContent className="p-3">
          <h4 className="font-semibold text-sm truncate">{nft.nft_item?.name}</h4>
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-1">
              <Star className="w-3 h-3 text-yellow-500" />
              <span className="text-xs">{nft.nft_item?.stars_value}</span>
            </div>
            <span className="text-xs text-muted-foreground">
              {nft.acquired_from}
            </span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );

  const CaseCard: React.FC<{ case: Case }> = ({ case: gameCase }) => (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <div className="aspect-square relative">
        <img
          src={gameCase.image_url}
          alt={gameCase.name}
          className="w-full h-full object-cover"
        />
        
        {/* Overlay для анимации открытия */}
        <AnimatePresence>
          {openingCase === gameCase.id && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/50 flex items-center justify-center"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-12 h-12 border-4 border-white border-t-transparent rounded-full"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      <CardContent className="p-4">
        <h3 className="font-bold mb-2">{gameCase.name}</h3>
        <p className="text-sm text-muted-foreground mb-3">{gameCase.description}</p>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 text-yellow-500" />
            <span className="font-semibold">{gameCase.price_stars}</span>
          </div>
          
          <Button
            size="sm"
            onClick={() => openCase(gameCase.id, gameCase.price_stars)}
            disabled={openingCase === gameCase.id || userBalance < gameCase.price_stars}
            className="flex items-center gap-2"
          >
            <Package className="w-4 h-4" />
            {openingCase === gameCase.id ? 'Открытие...' : 'Открыть'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Статистика коллекции */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <Trophy className="w-6 h-6 mx-auto mb-2 text-primary" />
            <div className="text-2xl font-bold">{nfts.length}</div>
            <div className="text-xs text-muted-foreground">Всего NFT</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <Star className="w-6 h-6 mx-auto mb-2 text-yellow-500" />
            <div className="text-2xl font-bold">
              {nfts.reduce((sum, nft) => sum + (nft.nft_item?.stars_value || 0), 0)}
            </div>
            <div className="text-xs text-muted-foreground">Общая стоимость</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <Eye className="w-6 h-6 mx-auto mb-2 text-green-500" />
            <div className="text-2xl font-bold">
              {nfts.filter(nft => nft.is_equipped).length}
            </div>
            <div className="text-xs text-muted-foreground">Экипировано</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <Sparkles className="w-6 h-6 mx-auto mb-2 text-purple-500" />
            <div className="text-2xl font-bold">
              {nfts.filter(nft => ['epic', 'legendary'].includes(nft.nft_item?.rarity || '')).length}
            </div>
            <div className="text-xs text-muted-foreground">Редких</div>
          </CardContent>
        </Card>
      </div>

      {/* Вкладки */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="collection" className="flex items-center gap-2">
            <Trophy className="w-4 h-4" />
            Коллекция
          </TabsTrigger>
          <TabsTrigger value="cases" className="flex items-center gap-2">
            <Package className="w-4 h-4" />
            Кейсы
          </TabsTrigger>
        </TabsList>

        <TabsContent value="collection" className="space-y-4">
          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="aspect-square bg-muted animate-pulse rounded-lg" />
              ))}
            </div>
          ) : nfts.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {nfts.map((nft) => (
                <NFTCard key={nft.id} nft={nft} />
              ))}
            </div>
          ) : (
            <Card className="p-12 text-center">
              <Trophy className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Коллекция пуста</h3>
              <p className="text-muted-foreground mb-4">
                Откройте первый кейс, чтобы начать коллекцию NFT!
              </p>
              <Button onClick={() => setSelectedTab('cases')}>
                Посмотреть кейсы
              </Button>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="cases" className="space-y-4">
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="aspect-square bg-muted animate-pulse rounded-lg" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {cases.map((gameCase) => (
                <CaseCard key={gameCase.id} case={gameCase} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Модальное окно с результатом открытия кейса */}
      <AnimatePresence>
        {lastDrop && (
          <Dialog open={!!lastDrop} onOpenChange={() => setLastDrop(null)}>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="text-center">🎉 Поздравляем!</DialogTitle>
              </DialogHeader>
              
              <div className="text-center space-y-4">
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: "spring", duration: 0.8 }}
                  className="relative mx-auto w-32 h-32"
                >
                  <img
                    src={lastDrop.nft_item?.image_url}
                    alt={lastDrop.nft_item?.name}
                    className="w-full h-full object-cover rounded-lg"
                  />
                  <div className={`absolute inset-0 border-4 ${rarityColors[lastDrop.nft_item?.rarity]} rounded-lg`} />
                </motion.div>
                
                <div>
                  <h3 className="text-xl font-bold">{lastDrop.nft_item?.name}</h3>
                  <Badge className={`${rarityColors[lastDrop.nft_item?.rarity]} text-white mt-2`}>
                    {rarityLabels[lastDrop.nft_item?.rarity]}
                  </Badge>
                </div>
                
                <div className="flex items-center justify-center gap-2">
                  <Star className="w-5 h-5 text-yellow-500" />
                  <span className="text-lg font-semibold">{lastDrop.total_value}</span>
                </div>
                
                <Button onClick={() => setLastDrop(null)} className="w-full">
                  Отлично!
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NFTCollection;
