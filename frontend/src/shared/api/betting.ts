import {http} from './http';
import {
    GameRoundSchema,
    CurrentRoundResponseSchema,
    BonusPerRoundRequestSchema,
    BonusPerRoundResponseSchema,
    BetSchema,
    CreateBetRequestSchema,
    CreateBetResponseSchema,
    NewsSchema,
    PaginatedResponseSchema,
    GameRoundsQuerySchema,
    BetsQuerySchema,
    NewsQuerySchema,
} from './schemas';
import type {z} from 'zod';

// Types
export type GameRound = z.infer<typeof GameRoundSchema>;
export type CurrentRoundResponse = z.infer<typeof CurrentRoundResponseSchema>;
export type BonusPerRoundRequest = z.infer<typeof BonusPerRoundRequestSchema>;
export type BonusPerRoundResponse = z.infer<typeof BonusPerRoundResponseSchema>;
export type Bet = z.infer<typeof BetSchema>;
export type CreateBetRequest = z.infer<typeof CreateBetRequestSchema>;
export type CreateBetResponse = z.infer<typeof CreateBetResponseSchema>;
export type News = z.infer<typeof NewsSchema>;
export type GameRoundsQuery = z.infer<typeof GameRoundsQuerySchema>;
export type BetsQuery = z.infer<typeof BetsQuerySchema>;
export type NewsQuery = z.infer<typeof NewsQuerySchema>;

// Game Rounds API
export const getGameRounds = async (query?: GameRoundsQuery) => {
    const validatedQuery = query ? GameRoundsQuerySchema.parse(query) : {};
    const params = new URLSearchParams();

    Object.entries(validatedQuery).forEach(([key, value]) => {
        if (value !== undefined) {
            params.append(key, String(value));
        }
    });

    const url = `/betting/rounds/${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await http.get(url);
    return PaginatedResponseSchema(GameRoundSchema).parse(response);
};

export const getGameRound = async (id: number): Promise<GameRound> => {
    const response = await http.get(`/betting/rounds/${id}/`);
    return GameRoundSchema.parse(response);
};

export const getCurrentRound = async (): Promise<CurrentRoundResponse> => {
    const response = await http.get('/betting/rounds/current/');
    return CurrentRoundResponseSchema.parse(response);
};

export const bonusPerRound = async (data: BonusPerRoundRequest): Promise<BonusPerRoundResponse> => {
    const validatedData = BonusPerRoundRequestSchema.parse(data);
    const response = await http.post('/betting/rounds/bonus_per_round/', validatedData);
    return BonusPerRoundResponseSchema.parse(response);
};

// Bets API
export const getBets = async (query?: any): Promise<any> => {
    const params = new URLSearchParams();

    if (query && typeof query === 'object') {
        Object.entries(query).forEach(([key, value]) => {
            if (value !== undefined) {
                params.append(key, String(value));
            }
        });
    }

    const url = `/betting/bets/${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await http.get(url);
    return response;
};

export const createBet = async (data: CreateBetRequest): Promise<CreateBetResponse> => {
    const validatedData = CreateBetRequestSchema.parse(data);
    const response = await http.post('/betting/bets/', validatedData);
    return CreateBetResponseSchema.parse(response);
};

export const getBet = async (id: number): Promise<Bet> => {
    const response = await http.get(`/betting/bets/${id}/`);
    return BetSchema.parse(response);
};

// News API
export const getNews = async (query?: NewsQuery) => {
    const validatedQuery = query ? NewsQuerySchema.parse(query) : {};
    const params = new URLSearchParams();

    Object.entries(validatedQuery).forEach(([key, value]) => {
        if (value !== undefined) {
            params.append(key, String(value));
        }
    });

    const url = `/betting/news/${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await http.get(url);
    return PaginatedResponseSchema(NewsSchema).parse(response);
};

export const getNewsItem = async (id: number): Promise<News> => {
    const response = await http.get(`/betting/news/${id}/`);
    return NewsSchema.parse(response);
};
