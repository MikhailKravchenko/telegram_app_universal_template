import {Link, useLocation} from '@tanstack/react-router';
import type {TIconMapKeys} from '@/assets/icons';
import {Icon} from '@/components/Icon';
import {useAtom} from 'jotai';
import {appAtom} from '@/atom/appAtom';
import {useTranslation} from 'react-i18next';

type NavItem = {
    path: string;
    labelKey: string;
    icon: TIconMapKeys;
};

const navItems: NavItem[] = [
    {
        path: '/',
        labelKey: 'nav.home',
        icon: 'forecasts',
    },
    {
        path: '/placeholder-1',
        labelKey: 'nav.placeholder1',
        icon: 'game',
    },
    {
        path: '/placeholder-2',
        labelKey: 'nav.placeholder2',
        icon: 'result',
    },
    {
        path: '/more',
        labelKey: 'nav.more',
        icon: 'more',
    },
];

export const BottomNavigation = () => {
    const {t} = useTranslation();
    const location = useLocation();
    const [app, setApp] = useAtom(appAtom);

    return (
        <div className="fixed bottom-0 left-0 right-0 backdrop-blur-md backdrop-filter bg-black/60 border-t border-stone-800 z-[70]">
            <div className="flex items-center">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path;

                    if (item.path === '/more') {
                        return (
                            <button
                                key={item.labelKey}
                                type="button"
                                onClick={() => setApp({...app, isShowSidebar: !app?.isShowSidebar})}
                                className="flex-1 flex flex-col items-center gap-1 p-3 min-h-0 min-w-0"
                            >
                                <Icon
                                    name={item.icon}
                                    stroke={app?.isShowSidebar ? 'var(--accent)' : 'var(--charcoal-grey)'}
                                />
                                <p
                                    style={{color: app?.isShowSidebar ? 'var(--accent)' : 'var(--charcoal-grey)'}}
                                    className={`font-medium text-xs text-center whitespace-nowrap tracking-[-0.24px] leading-4`}
                                >
                                    {t(item.labelKey)}
                                </p>
                            </button>
                        );
                    }

                    return (
                        <Link
                            key={item.labelKey}
                            to={item.path}
                            className="flex-1 flex flex-col items-center gap-1 p-3 min-h-0 min-w-0"
                        >
                            <Icon stroke={isActive ? 'var(--accent)' : 'var(--charcoal-grey)'} name={item.icon} />
                            <p
                                style={{color: isActive ? 'var(--accent)' : 'var(--charcoal-grey)'}}
                                className="font-medium text-xs text-center whitespace-nowrap tracking-[-0.24px] leading-4"
                            >
                                {t(item.labelKey)}
                            </p>
                        </Link>
                    );
                })}
            </div>
        </div>
    );
};
