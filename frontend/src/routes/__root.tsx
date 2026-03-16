import {createRootRoute, Outlet} from '@tanstack/react-router';
import {useAtom, useAtomValue} from 'jotai';
import {appAtom} from '@/atom/appAtom';
import {BottomNavigation, SidebarNavigation, Header} from '@/widgets';
import {userAtom} from '@/atom/userAtom.ts';
import {useTelegramWebApp} from '@/shared/lib';

const RootLayout = () => {
    const [app, setApp] = useAtom(appAtom);
    const user = useAtomValue(userAtom);
    const webApp = useTelegramWebApp();

    return (
        <>
            <Header coins={user?.balance?.coins_balance} userAvatar={webApp?.initDataUnsafe.user?.photo_url} />
            <div className="h-[calc(100vh-70px)] relative pt-[50px] overflow-y-scroll overflow-x-hidden">
                <Outlet />
            </div>
            <SidebarNavigation isOpen={!!app?.isShowSidebar} onClose={() => setApp({...app, isShowSidebar: false})} />
            <BottomNavigation />
        </>
    );
};

export const Route = createRootRoute({component: RootLayout});
