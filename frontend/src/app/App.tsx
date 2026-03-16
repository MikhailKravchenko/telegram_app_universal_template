import {RouterProvider, createRouter} from '@tanstack/react-router';
import TelegramProvider from './providers/TelegramProvider';
import AuthProvider from './providers/AuthProvider';
import {Provider as StoreProvider} from 'jotai';

import {routeTree} from '../routeTree.gen';
import {FlashMessageProvider} from '@/components/FlashMessage';

const router = createRouter({routeTree});

const App = () => {
    return (
        <TelegramProvider>
            <StoreProvider>
                <AuthProvider>
                    <FlashMessageProvider>
                        <RouterProvider router={router} />
                    </FlashMessageProvider>
                </AuthProvider>
            </StoreProvider>
        </TelegramProvider>
    );
};

export default App;
