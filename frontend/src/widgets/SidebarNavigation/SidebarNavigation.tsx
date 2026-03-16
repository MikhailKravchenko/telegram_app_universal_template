import {useEffect, useRef} from 'react';
import {useTranslation} from 'react-i18next';
import {SidebarLink} from './SidebarLink';

interface SidebarNavigationProps {
    isOpen: boolean;
    onClose: () => void;
}

// Simple left sidebar with slide-in animation
export const SidebarNavigation = ({isOpen, onClose}: SidebarNavigationProps) => {
    const panelRef = useRef<HTMLDivElement | null>(null);
    const {t} = useTranslation();

    // Prevent scrolling when open
    useEffect(() => {
        if (isOpen) {
            const prev = document.body.style.overflow;
            document.body.style.overflow = 'hidden';
            return () => {
                document.body.style.overflow = prev;
            };
        }
    }, [isOpen]);

    return (
        <>
            <div
                aria-hidden
                onClick={onClose}
                className={`fixed inset-0 bg-black/40 transition-opacity duration-300 z-[55] ${
                    isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
                }`}
            />
            {/* Panel */}
            <div
                ref={panelRef}
                role="dialog"
                aria-modal="true"
                className={`fixed top-0 left-0 h-full w-[84%] max-w-[344px] bg-black border-r border-stone-800 shadow-xl transition-transform duration-300 ease-out will-change-transform z-[60] ${
                    isOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
            >
                <nav className="h-full overflow-y-auto px-4 py-2 pb-24">
                    {/* Navigation items */}
                    <SidebarLink icon="game" label={t('nav.game')} to="/game" onClose={onClose} />
                    <SidebarLink icon="forecasts" label={t('nav.forecast')} to="/" onClose={onClose} />
                    <SidebarLink icon="result" label={t('nav.result')} to="/result" onClose={onClose} />

                    {/* Existing routes */}
                    <SidebarLink icon="tasks" label={t('nav.tasks')} to="/tasks" onClose={onClose} />
                    <SidebarLink icon="presale" label="Predict-To-Earn" to="/presale" onClose={onClose} />
                    <SidebarLink icon="profile" label={t('nav.profile')} to="/profile" onClose={onClose} />
                    <SidebarLink icon="rules" label={t('nav.rules')} to="/rules" onClose={onClose} />
                    <SidebarLink icon="help" label={t('nav.help')} to="/help" onClose={onClose} />

                    {/* Language settings */}
                    <SidebarLink icon="more" label={t('nav.language')} to="/language" onClose={onClose} />
                </nav>
            </div>
        </>
    );
};
