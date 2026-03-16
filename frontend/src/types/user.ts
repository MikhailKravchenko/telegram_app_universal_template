import type {TelegramLoginResponse} from '@/shared/api';

export type Balance = {
    coins_balance?: number;
    total_earned?: number;
    total_spent?: number;
    updated_at?: string;
};

export type TUser = {
    user: TelegramLoginResponse['user'];
    balance?: Balance;
};
