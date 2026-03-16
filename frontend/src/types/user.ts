import type {Balance, TelegramLoginResponse} from '@/shared/api';

export type TUser = {
    user: TelegramLoginResponse['user'];
    balance?: Balance;
};
