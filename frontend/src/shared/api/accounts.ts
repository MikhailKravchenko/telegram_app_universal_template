import {http} from './http';
import {
    TelegramLoginRequestSchema,
    TelegramLoginResponseSchema,
    TelegramAuthStatusSchema,
    LogoutResponseSchema,
    UserInfoSchema,
} from './schemas';
import {z} from 'zod';

// Types (auth + basic user info only)
export type TelegramLoginRequest = z.infer<typeof TelegramLoginRequestSchema>;
export type TelegramLoginResponse = z.infer<typeof TelegramLoginResponseSchema>;
export type TelegramAuthStatus = z.infer<typeof TelegramAuthStatusSchema>;
export type LogoutResponse = z.infer<typeof LogoutResponseSchema>;
export type UserInfo = z.infer<typeof UserInfoSchema>;

// Authentication API
export const telegramLogin = async (data: TelegramLoginRequest): Promise<TelegramLoginResponse> => {
    const validatedData = TelegramLoginRequestSchema.parse(data);
    const response = await http.post('/accounts/telegram/login/', validatedData);
    return TelegramLoginResponseSchema.parse(response);
};

export const getTelegramAuthStatus = async (): Promise<TelegramAuthStatus> => {
    const response = await http.get('/accounts/telegram/status/');
    return TelegramAuthStatusSchema.parse(response);
};

export const logout = async (): Promise<LogoutResponse> => {
    const response = await http.post('/accounts/logout/');
    return LogoutResponseSchema.parse(response);
};

// User API
export const getUserInfo = async (id?: number): Promise<UserInfo> => {
    const url = id ? `/accounts/users/${id}/` : '/accounts/users/';
    const response = await http.get(url);

    if (Array.isArray(response)) {
        const arr = z.array(UserInfoSchema).parse(response);
        if (arr.length === 0) {
            throw new Error('User not found');
        }
        return arr[0];
    }

    return UserInfoSchema.parse(response);
};
