import {useEffect, useMemo, useState} from 'react';
import {useAtomValue} from 'jotai';
import {useTranslation} from 'react-i18next';
import {userAtom} from '@/atom/userAtom';
import {Icon} from '@/components/Icon';
import {
    getBets,
    getInvestmentSummary,
    getReferralLink,
    getReferralStats,
    type InvestmentSummary,
    type ReferralStats,
} from '@/shared/api';
import {env} from '@/shared/config';
import {formatNumber, useTelegramWebApp} from '@/shared/lib';
import {BalanceCard} from './BalanceCard';
import {StatCard} from './StatCard';
import {getInitials} from '../utils/getInitials';
import {FriendRow} from './FriendRow';

export const ProfilePage = () => {
    const {t} = useTranslation();
    const user = useAtomValue(userAtom);
    const webApp = useTelegramWebApp();

    const [referralStats, setReferralStats] = useState<ReferralStats | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [investment, setInvestment] = useState<InvestmentSummary | null>(null);
    const [betsCount, setBetsCount] = useState(0);

    const displayName = useMemo(() => user?.user?.username || 'User', [user?.user?.username]);
    const avatarUrl = webApp?.initDataUnsafe.user?.photo_url;

    const load = async () => {
        setIsLoading(true);
        try {
            const [referralStats, investmentSummary, bets] = await Promise.all([
                getReferralStats(),
                getInvestmentSummary(),
                getBets(),
            ]);
            setReferralStats(referralStats);
            setBetsCount(bets.count);
            setInvestment(investmentSummary);
        } catch (e) {
            console.error('Failed to load profile data', JSON.stringify(e));
            alert('Failed to load profile data: ' + JSON.stringify(e));
        } finally {
            setIsLoading(false);
        }
    };

    const userLabel = useMemo(() => {
        if (referralStats) {
            if (referralStats.referrals_count >= 10) {
                return t('profile.labels.alpha');
            } else if (referralStats.referrals_count >= 25) {
                return t('profile.labels.adept');
            } else if (referralStats.referrals_count >= 50) {
                return t('profile.labels.operator');
            } else if (referralStats.referrals_count >= 100) {
                return t('profile.labels.architect');
            } else if (referralStats.referrals_count >= 250) {
                return t('profile.labels.legend');
            }
        }
        return null;
    }, [referralStats, t]);

    useEffect(() => {
        void load();
    }, []);

    const handleInvite = async () => {
        try {
            const link = await getReferralLink();
            const inviteLink = `${env.TELEGRAM_APP}?startapp=${link.telegram_id}`;

            // Prefer Telegram native method if available
            if (webApp?.openTelegramLink) {
                const shareText = t('profile.shareText');
                const fullUrl = `https://t.me/share/url?url=${encodeURIComponent(inviteLink)}&text=${encodeURIComponent(shareText)}`;
                webApp.openTelegramLink(fullUrl);
                return;
            } else if (navigator.share) {
                await navigator.share({
                    title: t('profile.shareTitle'),
                    text: t('profile.shareTitleShort'),
                    url: inviteLink,
                });
                return;
            }

            await navigator.clipboard.writeText(inviteLink);
            alert(t('profile.linkCopied'));
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="py-8 px-4 flex flex-col gap-8">
            {/* Top: avatar and name */}
            <div className="flex flex-col gap-2 items-center">
                <div className="w-[64px] h-[64px] rounded-full overflow-hidden bg-gradient-to-b from-[#4722ff] to-black">
                    {avatarUrl ? (
                        <img src={avatarUrl} alt="avatar" className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center txt-button-bold">
                            {getInitials(displayName)}
                        </div>
                    )}
                </div>
                <div className="txt-title-2">{displayName}</div>
                {userLabel && <div className="txt-body text-[var(--accent)]">{userLabel}</div>}
            </div>

            {/* Balance */}
            <BalanceCard balance={user?.balance?.coins_balance} />
            <div className="w-full flex flex-wrap gap-4">
                <StatCard label={t('profile.invitedFriends')} value={referralStats?.referrals_count ?? 0} />
                <StatCard label={t('profile.friendsBonus')} value={referralStats?.total_bonuses_earned ?? 0} />
            </div>

            {/* Invite button */}
            <button
                onClick={handleInvite}
                className="w-full rounded-[12px] px-7 py-4 bg-[var(--accent)] text-white txt-button-bold shadow-[0_0_0_2px_#ff835e]"
            >
                {t('profile.inviteButton')}
            </button>

            {/* List of your Friends */}
            <div className="w-full flex flex-col gap-4">
                <div className="w-full flex items-center justify-between">
                    <div className="txt-headline">{t('profile.friendsList')}</div>
                    <button
                        aria-label="refresh"
                        onClick={() => load()}
                        className="w-[26px] h-[26px] rounded-full flex items-center justify-center text-white/80 hover:text-white"
                    >
                        <Icon name="refresh" size={20} />
                    </button>
                </div>

                <div className="w-full rounded-[12px] border border-[var(--coffee-brown)] p-4 flex flex-col gap-4">
                    {isLoading && <div className="txt-body text-white/70">{t('common.loading')}</div>}
                    {!isLoading && (
                        <div className="flex flex-col">
                            {referralStats?.referrals_count === 0 && (
                                <div className="txt-body text-white/70">{t('profile.noFriends')}</div>
                            )}
                            {referralStats?.referrals.map((b, idx) => (
                                <FriendRow key={idx.toString()} index={idx + 1} name={b.username || ''} />
                            ))}
                        </div>
                    )}
                </div>
            </div>
            <div className="w-full flex flex-col gap-4">
                <div className="w-full rounded-[12px] border border-[var(--coffee-brown)] p-4">
                    <div className="txt-footnote text-[var(--charcoal-grey)]">{t('profile.totalForecasts')}</div>
                    <div className="txt-title-2 text-[var(--accent)] mt-1">{betsCount}</div>
                </div>

                <div className="w-full rounded-[12px] border border-[var(--coffee-brown)] p-4 flex flex-wrap gap-4">
                    <div className="flex-1 flex flex-col gap-1">
                        <div className="txt-footnote text-[var(--charcoal-grey)]">{t('profile.presaleInvested')}</div>
                        <div className="flex items-center gap-2">
                            <div className="txt-title-2 text-[var(--accent)]">
                                {formatNumber(investment?.total_invested ?? 0)}
                            </div>
                            <div className="txt-footnote text-[var(--charcoal-grey)]">{t('common.coins')}</div>
                        </div>
                    </div>
                    <div className="flex-1 flex flex-col gap-1">
                        <div className="txt-footnote text-[var(--charcoal-grey)]">{t('presale.youReceive')}</div>
                        <div className="flex items-center gap-2">
                            <div className="txt-title-2 text-[var(--accent)]">
                                {formatNumber(investment?.total_tokens ?? 0)}
                            </div>
                            <div className="txt-footnote text-[var(--charcoal-grey)]">{t('common.pulse')}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
