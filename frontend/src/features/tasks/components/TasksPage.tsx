import {useEffect, useState, useMemo} from 'react';
import {useTranslation} from 'react-i18next';
import {TaskCard} from './TaskCard';
import {
    claimSocialBonus,
    claimTelegramChannel2Bonus,
    claimTelegramChannel1Bonus,
    getBonusStatistics,
    type BonusStatistics,
} from '@/shared/api';
import {DefaultNotification, useFlashMessage} from '@/components/FlashMessage';

const taskLinks = {
    x: 'https://x.com/pulsepai?s=11',
    telegram1: 'https://t.me/Pulseplatformai',
    telegram2: 'https://t.me/Pulse_platform_ai',
};

export const TasksPage = () => {
    const {t} = useTranslation();
    const [bonusStats, setBonusStats] = useState<BonusStatistics | null>(null);
    const {setFlashMessage} = useFlashMessage();

    const fetchBonuses = async () => {
        const results = await getBonusStatistics();
        setBonusStats(results);
    };

    useEffect(() => {
        fetchBonuses();
    }, []);

    const dailyBonus = useMemo(() => bonusStats?.bonus_types_stats?.['daily_login']?.count ?? 0, [bonusStats]);
    const telegram1Bonus = useMemo(
        () => bonusStats?.bonus_types_stats?.['telegram_channel_1'].count ?? 0,
        [bonusStats],
    );

    const telegram2Bonus = useMemo(
        () => bonusStats?.bonus_types_stats?.['telegram_channel_2'].count ?? 0,
        [bonusStats],
    );

    const xBonus = useMemo(() => bonusStats?.bonus_types_stats?.['social_subscription'].count ?? 0, [bonusStats]);

    const openLink = (url: string) => {
        try {
            const w = window as any;
            if (url.startsWith('https://t.me/') && w?.Telegram?.WebApp?.openTelegramLink) {
                w.Telegram.WebApp.openTelegramLink(url);
            } else {
                window.open(url, '_blank', 'noopener,noreferrer');
            }
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (e) {
            // ignore
        }
    };

    // Common wrapper to handle claim flows and notifications
    const handleClaim = async (url: string, action: () => Promise<{message?: string}>) => {
        openLink(url);
        try {
            const result = await action();
            const msg = result?.message || 'Success';
            setFlashMessage({
                component: <DefaultNotification message={msg} />,
            });
        } catch (e) {
            const errMsg = (e as any)?.response?.data?.message || 'Failed to complete task';
            setFlashMessage({
                component: <DefaultNotification message={errMsg} />,
            });
        }
    };

    const claimTelegram1 = async () => handleClaim(taskLinks.telegram1, claimTelegramChannel1Bonus);

    const claimTelegram2 = async () => handleClaim(taskLinks.telegram2, claimTelegramChannel2Bonus);

    const claimX = async () => handleClaim(taskLinks.x, claimSocialBonus);

    return (
        <div className="pt-3 px-2 pb-4 flex flex-col gap-4">
            <p className="txt-title-2 text-center text-white">{t('tasks.title')}</p>
            <TaskCard amount={dailyBonus?.amount} title={t('tasks.daily')} icon="users" completed={!!dailyBonus} />
            <TaskCard
                amount={xBonus?.amount}
                title={t('tasks.subscribeX')}
                icon="x"
                onComplete={claimX}
                completed={!!xBonus}
            />
            <TaskCard
                amount={telegram1Bonus?.amount}
                title={t('tasks.subscribeTelegram1')}
                icon="telegram"
                onComplete={claimTelegram1}
                completed={!!telegram1Bonus}
            />
            <TaskCard
                amount={telegram2Bonus?.amount}
                title={t('tasks.subscribeTelegram2')}
                icon="telegram"
                onComplete={claimTelegram2}
                completed={!!telegram2Bonus}
            />
        </div>
    );
};
