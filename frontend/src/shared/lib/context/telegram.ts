import {createContext, useContext} from 'react';
import type {WebApp} from 'telegram-web-app';

export const TelegramContext = createContext<WebApp | null>(null);

export const useTelegramWebApp = () => {
    const context = useContext(TelegramContext);
    return context;
};
