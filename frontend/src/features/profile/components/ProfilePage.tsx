import {useMemo} from 'react';
import {useAtomValue} from 'jotai';
import {useTranslation} from 'react-i18next';
import {userAtom} from '@/atom/userAtom';
import {useAuth} from '@/shared/lib/context/auth';
import {useTelegramWebApp} from '@/shared/lib';
import {getInitials} from '../utils/getInitials';

export const ProfilePage = () => {
    const {t} = useTranslation();
    const user = useAtomValue(userAtom);
    const webApp = useTelegramWebApp();
    const {logout, isLoading} = useAuth();

    const displayName = useMemo(() => user?.user?.username || 'User', [user?.user?.username]);
    const avatarUrl = webApp?.initDataUnsafe.user?.photo_url;

    return (
        <div className="py-8 px-4 flex flex-col gap-8">
            <div className="flex flex-col gap-2 items-center">
                <div className="w-[64px] h-[64px] rounded-full overflow-hidden bg-gradient-to-b from-[#4722ff] to-black">
                    {avatarUrl ? (
                        <img src={avatarUrl} alt={t('profile.userAvatar')} className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center txt-button-bold">
                            {getInitials(displayName)}
                        </div>
                    )}
                </div>
                <div className="txt-title-2">{displayName}</div>
            </div>

            <button
                type="button"
                onClick={() => logout()}
                disabled={isLoading}
                className="w-full rounded-[12px] px-7 py-4 bg-[var(--accent)] text-white txt-button-bold disabled:opacity-60"
            >
                {t('profile.logout')}
            </button>
        </div>
    );
};
