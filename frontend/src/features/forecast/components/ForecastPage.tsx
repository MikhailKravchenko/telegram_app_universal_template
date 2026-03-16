import {useState, useEffect, useRef, useMemo} from 'react';
import {useAtom} from 'jotai';
import {useTranslation} from 'react-i18next';
import {getCurrentRound, createBet, type CurrentRoundResponse} from '@/shared/api';
import type {TIconMapKeys} from '@/assets/icons';
import {Icon} from '@/components/Icon';
import {useAuth} from '@/shared/lib';
import {userAtom} from '@/atom/userAtom.ts';
import {useFlashMessage} from '@/components/FlashMessage';
import {BetPlacedNotification} from './BetPlacedNotication';
import {InsufficientBalanceNotification} from './InsufficientBalanceNotification';

export const ForecastPage = () => {
    const {t} = useTranslation();
    const {isAuthenticated} = useAuth();
    const {setFlashMessage} = useFlashMessage();
    const [forecastType, setForecastType] = useState<'short' | 'long'>('short');
    const [sentiment, setSentiment] = useState<'positive' | 'negative' | null>(null);
    const [amount, setAmount] = useState<number | null>(200);
    const [showInputAmount, setShowInputAmount] = useState<boolean>(false);
    const [roundData, setRoundData] = useState<CurrentRoundResponse | null>(null);
    const [inputValue, setInputValue] = useState<string>('');
    const inputRef = useRef<HTMLInputElement | null>(null);

    const [remainingMs, setRemainingMs] = useState<number | null>(null);
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const [user, setUser] = useAtom(userAtom);

    const currentRound = useMemo(() => {
        if (!roundData) return null;
        return roundData.rounds.find((r) => r.round.round_type === forecastType)?.round;
    }, [roundData, forecastType]);

    const formatTime = (ms: number | null) => {
        if (ms === null) return '0s';
        if (ms <= 0) return '0s';
        const totalSeconds = Math.floor(ms / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        if (hours > 0) {
            return `${hours}h ${minutes}m ${seconds}s`;
        }
        return `${minutes}m ${seconds}s`;
    };

    useEffect(() => {
        if (isAuthenticated) {
            getCurrentRound().then(async (data) => {
                setRoundData(data);
            });
        }
    }, [isAuthenticated]);

    useEffect(() => {
        if (showInputAmount) {
            setInputValue(amount ? String(amount) : '');
            setTimeout(() => inputRef.current?.focus(), 0);
        }
    }, [showInputAmount]);

    // Countdown timer.svg to round.end_time or UTC midnight for daily
    useEffect(() => {
        if (!currentRound?.end_time) {
            setRemainingMs(null);
            return;
        }
        const target = new Date(currentRound.end_time).getTime();

        const update = () => {
            const diff = target - Date.now();
            setRemainingMs(diff > 0 ? diff : 0);
        };
        update(); // initialize immediately
        const id = setInterval(update, 1000);
        return () => clearInterval(id);
    }, [currentRound?.end_time, forecastType]);

    useEffect(() => {
        if (remainingMs === 0) {
            const timeoutId = setTimeout(() => {
                getCurrentRound().then((data) => {
                    if (data) {
                        setRoundData(data);
                    }
                });
            }, 5000);
            return () => clearTimeout(timeoutId);
        }
    }, [remainingMs]);

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

    const SentimentCard = ({type, label, icon}: {type: 'positive' | 'negative'; label: string; icon: TIconMapKeys}) => {
        const isActive = sentiment === type;

        return (
            <button
                type="button"
                onClick={() => {
                    setSentiment(type);
                }}
                className={`flex flex-col justify-center items-center gap-2.5 h-[150px] rounded-2xl w-full border transition-all ${
                    isActive
                        ? sentiment === 'positive'
                            ? 'bg-[var(--green)] border-[var(--light-green)]'
                            : 'bg-[var(--red)] border-[var(--soft-pink)]'
                        : 'border-[var(--accent)]'
                }`}
            >
                <Icon name={icon} size={40} stroke={isActive ? 'var(--white)' : 'var(--accent)'} />
                <span className={`txt-title-3 ${isActive ? 'text-white' : 'text-[var(--accent)]'}`}>{label}</span>
            </button>
        );
    };

    const submitCustomAmount = () => {
        const num = Number(inputValue);
        if (!Number.isFinite(num) || num <= 0) {
            // simple validation: keep focus if invalid
            inputRef.current?.focus();
            return;
        }
        setAmount(num);
        setShowInputAmount(false);
    };

    const handlePlaceBet = async () => {
        if (!sentiment || !amount || !currentRound?.id || isSubmitting) {
            return;
        }

        if ((user?.balance?.coins_balance || 0) < amount) {
            setFlashMessage({
                component: (
                    <InsufficientBalanceNotification balance={user?.balance?.coins_balance || 0} amount={amount} />
                ),
            });
            return;
        }

        setIsSubmitting(true);
        try {
            await createBet({
                round: currentRound.id,
                amount,
                choice: sentiment,
            });
            setFlashMessage({
                component: (
                    <BetPlacedNotification sentiment={sentiment} amount={amount} time={formatTime(remainingMs)} />
                ),
            });

            // Reset form after a successful bet
            setSentiment(null);
            setAmount(200);

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

            // Refetch the current round to update bet status
            const data = await getCurrentRound();
            if (data) {
                setRoundData(data);
            }
        } catch (error) {
            console.error('Failed to place bet:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="pt-8 px-6 gap-6 flex flex-col">
            {/* Tabs */}
            <div className="flex flex-col items-center gap-6">
                <div className="flex gap-6">
                    <button
                        className={`relative txt-title-3 ${forecastType === 'short' ? 'text-[var(--accent)]' : 'text-[var(--charcoal-grey)]'}`}
                        onClick={() => setForecastType('short')}
                    >
                        {t('forecast.short.tab')}
                        {forecastType === 'short' && (
                            <span className="absolute -bottom-1 left-0 right-0 h-[3px] bg-[var(--accent)] rounded-full" />
                        )}
                    </button>
                    <button
                        onClick={() => setForecastType('long')}
                        className={`relative txt-title-3 ${forecastType === 'long' ? 'text-[var(--accent)]' : 'text-[var(--charcoal-grey)]'}`}
                    >
                        {t('forecast.long.tab')}
                        {forecastType === 'long' && (
                            <span className="absolute -bottom-1 left-0 right-0 h-[3px] bg-[var(--accent)] rounded-full" />
                        )}
                    </button>
                </div>
                <div className="flex flex-col gap-2">
                    <p className="txt-headline text-white text-center">{t(`forecast.${forecastType}.title`)}</p>
                    <p className="txt-footnote text-center text-[var(--charcoal-grey)]">
                        {t(`forecast.${forecastType}.description`)}
                    </p>
                </div>
            </div>

            {/* Sentiment cards */}
            <div className="grid grid-cols-2 gap-4">
                <SentimentCard type="positive" label={t('forecast.positive')} icon="thumbUp" />
                <SentimentCard type="negative" label={t('forecast.negative')} icon="thumbDown" />
            </div>

            {/* Amount */}
            <div>
                <p className="txt-title-3 text-center text-[var(--charcoal-grey)] mb-3">{t('forecast.amountLabel')}</p>
                {showInputAmount ? (
                    <form
                        className="flex items-center justify-between gap-2"
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
                            placeholder={t('forecast.placeholder')}
                            className="flex-1 bg-transparent outline-none px-3 py-4 txt-button-bold text-[var(--charcoal-grey)] border border-[var(--coffee-brown)] rounded-[18px]"
                        />
                        <button
                            type="submit"
                            className="px-7 py-4 rounded-[18px] txt-button-bold bg-[var(--accent)] text-white"
                        >
                            {t('common.enter')}
                        </button>
                    </form>
                ) : (
                    <div className="flex items-center justify-between rounded-full border border-stone-700 px-1 py-1">
                        <AmountPill value={100} />
                        <AmountPill value={200} />
                        <AmountPill value={500} />
                        <AmountPill
                            value="enter"
                            label={
                                !amount || [100, 200, 500].includes(amount) ? (
                                    t('common.enter')
                                ) : (
                                    <span className="text-[var(--accent)]">{amount.toString()}</span>
                                )
                            }
                        />
                    </div>
                )}
            </div>

            {/* Timer */}
            <div className="flex items-center justify-center gap-2 text-[var(--accent)] txt-title-3">
                <Icon name="timer" />
                <span>{formatTime(remainingMs)}</span>
            </div>

            {/* CTA button */}
            <div>
                <button
                    type="button"
                    onClick={handlePlaceBet}
                    disabled={!sentiment || !amount || isSubmitting}
                    className="w-full rounded-2xl bg-[var(--accent)] text-white txt-button-bold py-4 shadow-[0_8px_24px_rgba(228,81,37,0.4)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isSubmitting ? t('forecast.placing') : t(`forecast.${forecastType}.button`)}
                </button>
            </div>
        </div>
    );
};
