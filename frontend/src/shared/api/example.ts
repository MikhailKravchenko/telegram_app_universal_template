// Example usage of the API (auth-only template)
import {
    telegramLogin,
    getTelegramAuthStatus,
    getUserInfo,
    type TelegramLoginRequest,
} from '@/shared/api';

export const exampleAuthFlow = async () => {
    try {
        const loginData: TelegramLoginRequest = {
            telegramData: 'telegram_auth_data_string',
            referredBy: 123, // optional
        };

        const loginResponse = await telegramLogin(loginData);
        console.log('Login successful:', loginResponse.user);

        const authStatus = await getTelegramAuthStatus();
        console.log('Auth status:', authStatus);

        const userInfo = await getUserInfo();
        console.log('User info:', userInfo);
    } catch (error) {
        console.error('Auth error:', error);
    }
};
