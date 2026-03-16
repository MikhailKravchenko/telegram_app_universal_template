import classNames from 'classnames';
import Logo from '@/assets/logo-game.svg?react';
import {Icon} from '@/components/Icon';
import {useTranslation} from 'react-i18next';
import s from './Header.module.css';

interface HeaderProps {
    coins?: number;
    userAvatar?: string;
    className?: string;
}

export const Header = ({
    coins,
    userAvatar = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="42" height="42" viewBox="0 0 42 42"><rect width="42" height="42" rx="21" fill="%23666"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif" font-size="18" fill="%23fff">U</text></svg>',
    className = '',
}: HeaderProps) => {
    const {t} = useTranslation();
    return (
        <div className={`fixed top-0 left-0 right-0 w-full z-50 ${className}`}>
            {/* Content container */}
            <div className="relative flex justify-between items-center px-3 py-2.5">
                {/* Logo on the left */}
                <div className="flex items-center">
                    <Logo className="h-full w-auto" />
                </div>

                <div className="flex items-center gap-3">
                    {typeof coins === 'number' && (
                        <div
                            className={classNames(s.balance, 'flex items-center gap-1.5 px-3 py-1.5 rounded-full')}
                            data-node-id="I840:13924;1:1148"
                        >
                            <Icon name="coins" size={16} className="shrink-0 text-white" />
                            <span className="text-white font-semibold text-[16px] leading-[16px] whitespace-nowrap">
                                {coins}
                            </span>
                        </div>
                    )}
                    {/* User avatar on the right */}
                    <div className="w-[42px] h-[42px] rounded-full overflow-hidden">
                        <img src={userAvatar} alt={t('profile.userAvatar')} className="w-full h-full object-cover" />
                    </div>
                </div>
            </div>
        </div>
    );
};
