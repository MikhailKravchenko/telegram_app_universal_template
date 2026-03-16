import {useEffect, useMemo, useRef, useState} from 'react';
import {RouterProvider, createRouter} from '@tanstack/react-router';
import TelegramProvider from './providers/TelegramProvider';
import AuthProvider from './providers/AuthProvider';
import {Provider as StoreProvider} from 'jotai';

// Import the generated route tree
import {routeTree} from '../routeTree.gen';
import {FlashMessageProvider} from '@/components/FlashMessage';
import {GameProvider} from '@/app/providers/GameProvider.tsx';
import SplashScreen from '@/components/SplashScreen';
import {useAuth} from '@/shared/lib/context/auth.ts';

// Create a new router instance
const router = createRouter({routeTree});

function AppContent() {
    const {isAuthenticated, isLoading} = useAuth();

    // Show splash only on the very first mount
    const [showSplash, setShowSplash] = useState(true);
    const [isStart, setIsStart] = useState(false);
    const [progress, setProgress] = useState(0);
    const startRef = useRef<number | null>(null);
    const MIN_MS = 3000; // Minimum splash duration

    // Compute target progress based on auth state
    const target = useMemo(() => {
        if (isAuthenticated) return 100;
        if (isLoading) return 70; // during login/user fetch
        return 0; // initial pre-auth
    }, [isAuthenticated, isLoading]);

    useEffect(() => {
        if (startRef.current == null) startRef.current = Date.now();
        const tickMs = 30;
        const id = setInterval(() => {
            setProgress((p) => {
                // ease towards target
                const next = p + Math.max(0.2, (target - p) * 0.07);
                return Math.min(next, target);
            });
        }, tickMs);
        return () => clearInterval(id);
    }, [target]);

    useEffect(() => {
        if (!showSplash) return;
        if (isAuthenticated && !isLoading && progress >= 99) {
            const elapsed = Date.now() - (startRef.current ?? Date.now());
            const left = Math.max(0, MIN_MS - elapsed);
            const to = setTimeout(() => {
                setProgress(100);
                setIsStart(true);
            }, left);
            return () => clearTimeout(to);
        }
    }, [isAuthenticated, isLoading, progress, showSplash]);

    return (
        <>
            <RouterProvider router={router} />
            {showSplash && <SplashScreen progress={progress} isStart={isStart} onStart={() => setShowSplash(false)} />}
        </>
    );
}

const App = () => {
    return (
        <TelegramProvider>
            <StoreProvider>
                <AuthProvider>
                    <FlashMessageProvider>
                        <GameProvider>
                            <AppContent />
                        </GameProvider>
                    </FlashMessageProvider>
                </AuthProvider>
            </StoreProvider>
        </TelegramProvider>
    );
};

export default App;
