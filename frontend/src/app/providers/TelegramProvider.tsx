import {TelegramContext} from '@/shared/lib/context/telegram.ts';
import {type FC, type PropsWithChildren, useEffect, useState} from 'react';
import type {WebApp} from 'telegram-web-app';

const waitForTelegramWebApp = (timeout = 5000): Promise<WebApp> => {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        const check = () => {
            if (window.Telegram && window.Telegram.WebApp) {
                resolve(window.Telegram.WebApp);
            } else if (Date.now() - startTime >= timeout) {
                reject(new Error('Timeout waiting for Telegram WebApp'));
            } else {
                setTimeout(check, 100);
            }
        };
        check();
    });
};

const TelegramProvider: FC<PropsWithChildren> = ({children}) => {
    const [webApp, setWebApp] = useState<WebApp | null>(null);

    useEffect(() => {
        const applyHeaderColorBlack = (wa: WebApp) => {
            try {
                // Prefer explicit black header if supported by the current SDK
                wa.setHeaderColor('#000000');
            } catch {
                // Fallback to a darker system color key (older SDKs only accept preset keys)
                wa.setHeaderColor?.('secondary_bg_color' as any);
            }
        };

        const initializeTelegramWebApp = async () => {
            const webApp = await waitForTelegramWebApp();
            setWebApp(webApp);
            webApp.ready();
            webApp.expand();
            webApp.lockOrientation();
            webApp.disableVerticalSwipes();
            webApp.setBackgroundColor('#000');
            applyHeaderColorBlack(webApp);

            // Ensure header remains black if user switches theme in Telegram settings
            webApp.onEvent?.('themeChanged', () => applyHeaderColorBlack(webApp));
        };
        const scriptId = 'telegram-web-app';

        if (!document.getElementById(scriptId)) {
            const script = document.createElement('script');
            script.id = scriptId;
            script.src = 'https://telegram.org/js/telegram-web-app.js';
            script.async = true;
            script.onload = initializeTelegramWebApp;
            script.onerror = () => console.error('Failed to load Telegram WebApp SDK');
            document.head.appendChild(script);
        } else {
            initializeTelegramWebApp();
        }
    }, []);

    return <TelegramContext.Provider value={webApp}>{children}</TelegramContext.Provider>;
};

export default TelegramProvider;
