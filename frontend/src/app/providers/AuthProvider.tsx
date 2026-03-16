import {type FC, type PropsWithChildren, useEffect, useState} from 'react';
import {useAtom} from 'jotai';
import {AuthContext, type AuthContextType} from '@/shared/lib/context/auth.ts';
import {tokenAtom} from '@/atom/tokenAtom';
import {userAtom} from '@/atom/userAtom';
import {telegramLogin, getUserInfo, type TelegramLoginRequest} from '@/shared/api';
import type {TUser} from '@/types/user';
import {useTelegramWebApp} from '@/shared/lib';
import {env} from '@/shared/config';

const AuthProvider: FC<PropsWithChildren> = ({children}) => {
    const [token, setToken] = useAtom(tokenAtom);
    const [user, setUser] = useAtom(userAtom);
    const [isLoading, setIsLoading] = useState(false);
    const webApp = useTelegramWebApp();

    // Check if a user is authenticated based on token presence
    const isAuthenticated = Boolean(token && user);

    // Login function using Telegram data
    const login = async (data: TelegramLoginRequest) => {
        try {
            setIsLoading(true);

            // Call Telegram login API
            const response = await telegramLogin(data);
            console.log('RESPONSE', response);

            // Set access_token cookie on the configured domain
            const maxAge = 7 * 24 * 60 * 60; // 7 days
            const cookieAttrs = [`Path=/`, `Max-Age=${maxAge}`];
            if (env.APP_DOMAIN) cookieAttrs.push(`Domain=${env.APP_DOMAIN}`);
            if (env.NODE_ENV === 'production') {
                cookieAttrs.push('Secure', 'SameSite=None');
            } else {
                cookieAttrs.push('SameSite=Lax');
            }
            document.cookie = `access_token=${response.access}; ${cookieAttrs.join('; ')}`;

            // Save an access token to atom
            setToken(response.access);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Login failed';
            console.log('Login error: ' + errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    // Logout function
    const logout = async () => {
        try {
            setIsLoading(true);

            // Remove access_token cookie
            const deleteAttrs = ['Path=/', 'Max-Age=0'];
            if (env.APP_DOMAIN) deleteAttrs.push(`Domain=${env.APP_DOMAIN}`);
            document.cookie = `access_token=; ${deleteAttrs.join('; ')}`;

            // Clear tokens and user data
            setToken(null);
            setUser(null);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Logout failed';
            console.log('Error: ' + errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    // Seamless authentication on mount
    useEffect(() => {
        const runAuth = async () => {
            // 1) Try to restore token from cookie first
            if (!token) {
                const cookieToken = document.cookie
                    .split('; ')
                    .find((row) => row.startsWith('access_token='))
                    ?.split('=')[1];
                if (cookieToken) {
                    try {
                        setToken(decodeURIComponent(cookieToken));
                        // Let effect re-run with the new token to fetch the user
                        return;
                    } catch (err: unknown) {
                        console.error('Failed to decode access token from cookie', err);
                        // If decoding fails, still try raw value
                        setToken(cookieToken);
                        return;
                    }
                }
            }

            if (!token && webApp?.initData) {
                try {
                    setIsLoading(true);

                    // Automatically login using Telegram WebApp initData
                    await login({
                        telegramData: webApp.initData,
                        referredBy: webApp.initDataUnsafe.start_param
                            ? Number(webApp.initDataUnsafe.start_param)
                            : undefined,
                    });
                } catch (err) {
                    console.error('Seamless auth failed:', err);
                } finally {
                    setIsLoading(false);
                }
            }
            // If token exists but no user data, fetch user info
            else if (token && !user) {
                try {
                    setIsLoading(true);

                    // Get user info (which already includes balance)
                    const userInfo = await getUserInfo();
                    // Create a user object using the response structure
                    const userData: TUser = {
                        user: {
                            id: userInfo.id,
                            username: userInfo.username,
                            telegram_id: userInfo.telegram_id,
                            first_name: '', // UserInfo doesn't have these fields
                            last_name: '', // We'll use empty strings for now
                        },
                        balance: userInfo.balance,
                    };

                    setUser(userData);
                } catch (err) {
                    // If 401 error and we have Telegram data, try to re-login
                    if (err && typeof err === 'object' && 'status' in err && err.status === 401 && webApp?.initData) {
                        console.log('Token expired, attempting re-login...');
                        await logout();
                    } else {
                        // If a token is invalid, clear it
                        console.error('Auth check failed (getUserInfo):', err);
                        setToken(null);
                        setUser(null);
                    }
                } finally {
                    setIsLoading(false);
                }
            }
        };

        runAuth();
    }, [token, user, webApp?.initData]);

    const contextValue: AuthContextType = {
        isAuthenticated,
        isLoading,
        login,
        logout,
    };

    return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

export default AuthProvider;
