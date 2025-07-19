export interface Player {
  id: string;
  telegram_id: string;
  username: string;
  balance: number;
  status: 'waiting' | 'ready' | 'playing' | 'disconnected';
  bet_amount: number;
  is_creator: boolean;
}

export interface Room {
  id: string;
  game_type: 'dice' | 'cards' | 'rps';
  status: 'waiting' | 'playing' | 'finished' | 'cancelled';
  players: Player[];
  max_players: number;
  min_players: number;
  bet_amount: number;
  pot: number;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  timer_seconds: number;
  game_seed?: string;
  game_state: any;
  winner_ids: string[];
}

export interface CreateRoomRequest {
  player_id: string;
  telegram_id: string;
  username: string;
  game_type: 'dice' | 'cards' | 'rps';
  bet_amount: number;
}

export interface JoinRoomRequest {
  player_id: string;
  telegram_id: string;
  username: string;
  room_id: string;
}

class GameAPIService {
  private baseUrl = 'http://localhost:8000/api';

  async createRoom(request: CreateRoomRequest): Promise<{ room: Room; invite_link: string }> {
    const response = await fetch(`${this.baseUrl}/rooms/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to create room: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  }

  async joinRoom(request: JoinRoomRequest): Promise<{ room: Room }> {
    const response = await fetch(`${this.baseUrl}/rooms/join`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to join room: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  }

  async getAvailableRooms(gameType: string, maxBet?: number): Promise<Room[]> {
    let url = `${this.baseUrl}/rooms/available/${gameType}`;
    if (maxBet !== undefined) {
      url += `?max_bet=${maxBet}`;
    }

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to get available rooms: ${response.statusText}`);
    }

    const data = await response.json();
    return data.rooms;
  }

  async getRoomInfo(roomId: string): Promise<Room> {
    const response = await fetch(`${this.baseUrl}/rooms/${roomId}`);

    if (!response.ok) {
      throw new Error(`Failed to get room info: ${response.statusText}`);
    }

    const data = await response.json();
    return data.room;
  }

  async setPlayerReady(roomId: string, playerId: string): Promise<{ room: Room }> {
    const response = await fetch(`${this.baseUrl}/rooms/${roomId}/ready`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ player_id: playerId }),
    });

    if (!response.ok) {
      throw new Error(`Failed to set player ready: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  }

  async getPlayerStatus(playerId: string): Promise<{
    player_id: string;
    current_room: string | null;
    is_connected: boolean;
    room_info: Room | null;
  }> {
    const response = await fetch(`${this.baseUrl}/player/${playerId}/status`);

    if (!response.ok) {
      throw new Error(`Failed to get player status: ${response.statusText}`);
    }

    return await response.json();
  }

  async getDebugInfo(): Promise<{
    rooms: Record<string, Room>;
    matchmaker_queue: Record<string, string[]>;
    active_connections: number;
  }> {
    const response = await fetch(`${this.baseUrl}/debug/rooms`);

    if (!response.ok) {
      throw new Error(`Failed to get debug info: ${response.statusText}`);
    }

    return await response.json();
  }
}

export const gameAPI = new GameAPIService();
