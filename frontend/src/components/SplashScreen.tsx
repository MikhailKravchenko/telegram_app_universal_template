import React from 'react';
import {useTranslation} from 'react-i18next';
import Logo from '@/assets/logo-game.svg?react';

interface SplashScreenProps {
    progress: number;
    isStart: boolean;
    onStart: () => void;
}

// Accent color from design
const ACCENT = '#E45125';
const ACCENT_TEXT = '#fda41b';

const SplashScreen: React.FC<SplashScreenProps> = ({progress, isStart, onStart}) => {
    const {t} = useTranslation();
    const pct = Math.max(0, Math.min(100, Math.round(progress)));

    return (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black text-white">
            {/* Top header mimic (title) */}
            <div className="absolute top-14 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1">
                <Logo />
            </div>

            {/* Big glowing circle with percentage */}
            <div className="relative">
                {/* Outer glow */}
                <div
                    className="absolute -inset-16 rounded-full blur-2xl"
                    style={{background: `radial-gradient(closest-side, rgba(228,81,37,0.35), transparent 70%)`}}
                    aria-hidden
                />
                {/* Middle ring */}
                <div
                    onClick={isStart ? () => onStart() : () => {}}
                    className="relative w-[260px] h-[260px] rounded-full cursor-pointer"
                    style={{
                        background: 'radial-gradient(120px 120px at 50% 45%, rgba(253,164,27,0.25), rgba(0,0,0,0.9))',
                        boxShadow: `0 0 30px rgba(228,81,37,0.35)`,
                        border: `2px solid ${ACCENT}`,
                    }}
                >
                    {/* Percentage */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-[27.2px] font-bold" style={{color: ACCENT_TEXT}}>
                            {isStart ? 'START' : `${pct}%`}
                        </div>
                    </div>
                </div>
            </div>

            {/* Loading label at bottom */}
            <div className="absolute bottom-24 w-full text-button-bold opacity-90 text-center">
                {isStart ? t('common.welcome') : t('common.loading')}
            </div>

            {/* Bottom gradient vignette */}
            <div
                className="pointer-events-none absolute bottom-0 left-0 right-0 h-1/3"
                style={{
                    background: 'linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(228,81,37,0.35) 100%)',
                }}
                aria-hidden
            />
        </div>
    );
};

export default SplashScreen;
