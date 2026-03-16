import {useEffect, useMemo, useRef, useState} from 'react';
import {useAtom} from 'jotai';
import {useTranslation} from 'react-i18next';
import {
    type CurrentPresaleResponse,
    createInvestment,
    getCurrentPresale,
    getInvestmentSummary,
    type InvestmentSummary,
} from '@/shared/api/presale';
import {formatNumber} from '@/shared/lib';
import {DefaultNotification, useFlashMessage} from '@/components/FlashMessage';
import {PresaleBoughtNotification} from './PresaleBoughtNotification';
import {InsufficientBalanceNotification} from './InsufficientBalanceNotification';
import {userAtom} from '@/atom/userAtom';

export const PresalePage = () => {
    const {t} = useTranslation();
    const [presale, setPresale] = useState<CurrentPresaleResponse | null>(null);
    const [investment, setInvestment] = useState<InvestmentSummary | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [amount, setAmount] = useState<number | null>(500);
    const [showInputAmount, setShowInputAmount] = useState<boolean>(false);
    const [inputValue, setInputValue] = useState<string>('');
    const inputRef = useRef<HTMLInputElement | null>(null);
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const {setFlashMessage} = useFlashMessage();
    const [user, setUser] = useAtom(userAtom);

    useEffect(() => {
        (async () => {
            try {
                setLoading(true);
                const resultPresale = await getCurrentPresale();
                setPresale(resultPresale);
                const resultInvestment = await getInvestmentSummary();
                setInvestment(resultInvestment);
            } catch (e) {
                console.error('Failed to load current presale', e);
                setError('Failed to load data');
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    // Round info derived values (best-effort, tied to API fields if present)
    const roundInfo = useMemo(() => {
        if (!presale) return null;
        const totalRounds = presale.total_rounds;
        const currentRound = presale.current_round;
        const tokenPrice = presale.current_round_info?.tokens_per_coin;
        const totalInvested = presale.total_invested;
        const targetInvestment = presale.current_round_info?.target_investment;
        const remainingInvestment = presale.current_round_info?.remaining_investment;

        let daysLeft: number | undefined = undefined;
        if (presale.end_time) {
            const end = new Date(presale.end_time).getTime();
            const now = Date.now();
            if (Number.isFinite(end)) {
                const diffMs = end - now;
                if (diffMs > 0) {
                    daysLeft = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
                } else {
                    daysLeft = 0;
                }
            }
        }

        return {
            totalRounds,
            currentRound,
            daysLeft,
            tokenPrice,
            totalInvested,
            targetInvestment,
            remainingInvestment,
        };
    }, [presale]);

    useEffect(() => {
        if (showInputAmount) {
            setInputValue(amount ? String(amount) : '');
            setTimeout(() => inputRef.current?.focus(), 0);
        }
    }, [showInputAmount]);

    const AmountPill = ({value, label}: {value: number | 'enter'; label?: string | React.ReactElement}) => {
        const isActive = amount === value;
        return (
            <button
                type="button"
                onClick={() => {
                    if (typeof value === 'number') {
                        setAmount(value);
                        setShowInputAmount(false);
                    } else {
                        setShowInputAmount(true);
                    }
                }}
                className={`flex-1 h-10 rounded-[14px] transition-colors ${
                    isActive ? 'border border-[var(--accent)] bg-[#65210A] text-white' : 'text-[var(--charcoal-grey)]'
                }`}
            >
                {label ?? value}
            </button>
        );
    };

    const submitCustomAmount = () => {
        const num = Number(inputValue);
        if (!Number.isFinite(num) || num <= 0) {
            inputRef.current?.focus();
            return;
        }
        setAmount(num);
        setShowInputAmount(false);
    };

    const handleBuy = async () => {
        if (!amount || isSubmitting) return;
        const balance = user?.balance?.coins_balance ?? 0;
        if (amount > balance) {
            setFlashMessage({
                component: <InsufficientBalanceNotification balance={balance} />,
            });
            return;
        }
        try {
            setIsSubmitting(true);
            const result = await createInvestment({amount});
            setFlashMessage({
                component: <PresaleBoughtNotification amount={Number(result.tokens_received)} />,
            });
            setUser((prev) =>
                prev
                    ? {
                          ...prev,
                          balance: prev.balance
                              ? {...prev.balance, coins_balance: prev.balance.coins_balance - amount}
                              : undefined,
                      }
                    : null,
            );
            const res = await getCurrentPresale();
            setPresale(res);
        } catch (e) {
            setFlashMessage({
                component: (
                    <DefaultNotification message={(e as any).response?.data?.detail || 'Failed to create investment'} />
                ),
            });
            setError('Failed to create investment');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="pt-8 px-4 gap-8 flex flex-col" data-node-id="840:13692">
            {/* Title */}
            <p className="txt-title-2 text-center text-white">{t('presale.title')}</p>

            {/* Card - Spend / Receive / Buy */}
            <div
                className="w-full rounded-[12px] border border-[var(--coffee-brown)] px-4 py-6 flex flex-col gap-8"
                style={{
                    backgroundImage:
                        'linear-gradient(175.991deg, #000000 87.959%, #E45125 109.21%), linear-gradient(90deg, #1E1E20 0%, #1E1E20 100%)',
                }}
            >
                {/* Spend */}
                <div className="flex flex-col gap-2">
                    <div className="txt-body text-center text-[var(--charcoal-grey)]">{t('presale.youSpend')}</div>
                    {!showInputAmount ? (
                        <div className="flex items-center justify-between rounded-[18px] border border-[var(--coffee-brown)] gap-2">
                            <AmountPill value={500} />
                            <AmountPill value={1000} />
                            <AmountPill value={5000} />
                            <AmountPill
                                value="enter"
                                label={
                                    !amount || [500, 1000, 5000].includes(amount) ? (
                                        t('common.enter')
                                    ) : (
                                        <span className="text-[var(--accent)]">{amount.toString()}</span>
                                    )
                                }
                            />
                        </div>
                    ) : (
                        <form
                            className="flex w-full items-center justify-between gap-2 overflow-hidden"
                            onSubmit={(e) => {
                                e.preventDefault();
                                submitCustomAmount();
                            }}
                        >
                            <input
                                ref={inputRef}
                                type="number"
                                inputMode="numeric"
                                pattern="[0-9]*"
                                min={1}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder={t('presale.enterAmount')}
                                className="min-w-0 flex-1 bg-transparent outline-none px-3 py-4 txt-button-bold text-[var(--charcoal-grey)] border border-[var(--coffee-brown)] rounded-[18px]"
                            />
                            <button
                                type="submit"
                                className="px-7 py-4 rounded-[18px] txt-button-bold bg-[var(--accent)] text-white"
                            >
                                {t('common.enter')}
                            </button>
                        </form>
                    )}
                </div>

                {/* Receive */}
                <div className="flex flex-col items-center gap-2">
                    <p className="txt-body text-[var(--charcoal-grey)]">{t('presale.youReceive')}</p>
                    <div className="flex items-center gap-2">
                        <span className="txt-title-2 text-[var(--accent)]">
                            {formatNumber((amount ?? 0) * (roundInfo?.tokenPrice ?? 0))}
                        </span>
                        <span className="txt-title-2 text-white">{t('common.pulse')}</span>
                    </div>
                </div>

                {/* Buy button */}
                <button
                    onClick={handleBuy}
                    disabled={isSubmitting || !amount}
                    className={`self-center rounded-[12px] px-7 py-4 txt-button-bold shadow-[0_0_0_2px_#FF835E] ${
                        isSubmitting || !amount
                            ? 'bg-[var(--coffee-brown)] text-[var(--charcoal-grey)]'
                            : 'bg-[var(--accent)] text-white'
                    }`}
                >
                    {isSubmitting ? t('presale.processing') : t('presale.buyButton')}
                </button>
            </div>

            {/* Round Info */}
            <div className="flex flex-col gap-4">
                <p className="txt-headline text-white">{t('presale.roundInfo')}</p>
                <div className="w-full rounded-[12px] border border-[var(--coffee-brown)] p-4 flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                        <span className="txt-body text-[var(--charcoal-grey)]">{t('presale.round')}</span>
                        <span className="txt-subhead text-[var(--accent)]">
                            {loading
                                ? '…'
                                : error || !roundInfo?.currentRound || !roundInfo?.totalRounds
                                  ? '-'
                                  : `${roundInfo.currentRound} of ${roundInfo.totalRounds}`}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="txt-body text-[var(--charcoal-grey)]">{t('presale.daysLeft')}</span>
                        <span className="txt-subhead text-[var(--accent)]">
                            {loading
                                ? '…'
                                : error || roundInfo?.daysLeft === undefined
                                  ? '-'
                                  : formatNumber(roundInfo.daysLeft)}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="txt-body text-[var(--charcoal-grey)]">{t('presale.tokenPrice')}</span>
                        <span className="txt-subhead text-[var(--accent)]">
                            {loading
                                ? '…'
                                : error || roundInfo?.tokenPrice === undefined
                                  ? '-'
                                  : formatNumber(roundInfo.tokenPrice)}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="txt-body text-[var(--charcoal-grey)]">{t('presale.tokenForSale')}</span>
                        <span className="txt-subhead text-[var(--accent)]">
                            {loading
                                ? '…'
                                : error ||
                                    roundInfo?.remainingInvestment === undefined ||
                                    roundInfo?.targetInvestment === undefined
                                  ? '-'
                                  : `${formatNumber(roundInfo.remainingInvestment)} of ${formatNumber(roundInfo.targetInvestment)}`}
                        </span>
                    </div>
                </div>
            </div>

            {/* My Investments (static for now, per task) */}
            <div className="flex flex-col gap-4">
                <p className="txt-headline text-white">{t('presale.myInvestments')}</p>
                <div className="w-full rounded-[12px] border border-[var(--coffee-brown)] p-4 flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                        <span className="txt-body text-[var(--charcoal-grey)]">{t('presale.investedCoin')}</span>
                        <span className="txt-subhead text-[var(--accent)]">
                            {formatNumber(investment?.total_invested ?? 0)}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="txt-body text-[var(--charcoal-grey)]">{t('presale.tokensReceived')}</span>
                        <span className="txt-subhead text-[var(--accent)]">
                            {formatNumber(investment?.total_tokens ?? 0)}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="txt-body text-[var(--charcoal-grey)]">{t('presale.averageRate')}</span>
                        <span className="txt-subhead text-[var(--accent)]">
                            1 coin → {1 / Number(investment?.average_rate ?? 0)} Pulse
                        </span>
                    </div>
                    {/*<div className="flex items-center justify-between">*/}
                    {/*    <span className="txt-body text-[var(--charcoal-grey)]">Potential Cost</span>*/}
                    {/*    <span className="txt-subhead text-[var(--accent)]">+4,2k</span>*/}
                    {/*</div>*/}
                    {/*<div className="flex items-center justify-between">*/}
                    {/*    <span className="txt-body text-[var(--charcoal-grey)]">Potential Profit</span>*/}
                    {/*    <span className="txt-subhead text-[var(--accent)]">*/}
                    {/*        +3700 <span style={{color: 'var(--light-green)'}}>+1440%</span>*/}
                    {/*    </span>*/}
                    {/*</div>*/}
                </div>
            </div>

            {/* Info */}
            <div className="flex flex-col gap-4">
                <p className="txt-headline text-white">{t('presale.info')}</p>
                <div className="flex gap-4 flex-wrap">
                    <div className="min-w-[150px] flex-1 rounded-[12px] border border-[var(--coffee-brown)] p-4 flex flex-col gap-1">
                        <span className="txt-footnote text-[var(--charcoal-grey)]">{t('presale.totalInvested')}</span>
                        <span className="txt-title-2 text-[var(--accent)]">
                            {loading ? '…' : error ? '-' : formatNumber(roundInfo?.totalInvested || 0)}
                        </span>
                    </div>
                    <div className="min-w-[150px] flex-1 rounded-[12px] border border-[var(--coffee-brown)] p-4 flex flex-col gap-1">
                        <span className="txt-footnote text-[var(--charcoal-grey)]">{t('presale.nextRound')}</span>
                        <span className="txt-title-2 text-[var(--accent)]">
                            {loading ? '…' : error ? '-' : formatNumber(roundInfo?.remainingInvestment)}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};
