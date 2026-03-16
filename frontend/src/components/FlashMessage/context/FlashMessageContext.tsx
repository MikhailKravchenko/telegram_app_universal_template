import React, {createContext, useContext, useMemo, useState} from 'react';
import FlashMessage from '../FlashMessage.tsx';

export type FlashMessageData = {
    component: React.ReactNode;
};

type FlashMessageContextType = {
    flashMessage: FlashMessageData | null;
    setFlashMessage: (data: FlashMessageData | null) => void;
};

const FlashMessageContext = createContext<FlashMessageContextType | undefined>(undefined);

export const FlashMessageProvider: React.FC<React.PropsWithChildren> = ({children}) => {
    const [flashMessage, setFlashMessage] = useState<FlashMessageData | null>(null);

    const value = useMemo(() => ({flashMessage, setFlashMessage}), [flashMessage]);

    return (
        <FlashMessageContext.Provider value={value}>
            <FlashMessage>{children}</FlashMessage>
        </FlashMessageContext.Provider>
    );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useFlashMessage = () => {
    const ctx = useContext(FlashMessageContext);
    if (!ctx) throw new Error('useFlashMessage must be used within FlashMessageProvider');
    return ctx;
};
