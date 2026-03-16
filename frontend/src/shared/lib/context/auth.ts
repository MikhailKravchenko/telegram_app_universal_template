import {createContext, useContext} from 'react';
import type {TelegramLoginRequest} from '@/shared/api';

export interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (data: TelegramLoginRequest) => Promise<void>;
    logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
