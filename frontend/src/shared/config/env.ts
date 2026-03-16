export const env = {
    API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
    NODE_ENV: import.meta.env.VITE_NODE_ENV || 'development',
    APP_DOMAIN: import.meta.env.VITE_APP_DOMAIN,
    TELEGRAM_APP: import.meta.env.VITE_TELEGRAM_APP,
} as const;
