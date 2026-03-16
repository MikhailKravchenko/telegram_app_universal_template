import {useEffect, useMemo, useState} from 'react';
import {Icon} from '@/components/Icon';
import {getBet, type Bet, getGameRound, type GameRound} from '@/shared/api';
import {useParams} from '@tanstack/react-router';
import {ResultCard} from '@/features/result/components/ResultCard.tsx';

// Helper to format numbers with k suffix like in the design (e.g., 130k)
const formatK = (n?: number | null) => {
    if (n === undefined || n === null || isNaN(Number(n))) return '—';
    const v = Math.abs(Number(n));
    if (v >= 1000) {
        return `${Math.round(v / 100) / 10}k`;
    }
    return String(v);
};

export const ResultDetailsPage = () => {
    const {id} = useParams({from: '/result/$id'});
    const [bet, setBet] = useState<Bet | null>(null);
    const [round, setRound] = useState<GameRound | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const load = async () => {
            try {
                const b = await getBet(Number(id));
                setBet(b);
                // Fetch round for extra stats (pots/percents) if available
                try {
                    const r = await getGameRound(b.round);
                    setRound(r);
                } catch {
                    // optional; ignore
                }
            } catch (e) {
                setError('Failed to load bet');
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [id]);

    const {
        titleText,
        amountText,
        amountClass,
        tagText,
        tagClass,
        winnersPct,
        losersPct,
        totalWinnings,
        totalLosersLost,
    } = useMemo(() => {
        if (!bet) {
            return {
                titleText: '',
                amountText: '',
                amountClass: '',
                tagText: '',
                tagClass: '',
                winnersPct: undefined as number | undefined,
                losersPct: undefined as number | undefined,
                totalWinnings: undefined as number | undefined,
                totalLosersLost: undefined as number | undefined,
            };
        }
        const resolved = bet.round_result; // 'positive' | 'negative' | null
        const isWon = !!resolved && resolved === bet.choice;
        const amt = isWon ? (bet.payout_amount ?? 0) : -(bet.amount ?? 0);
        const amountText = `${isWon ? '' : '-'}${Math.abs(Math.round(amt))}`;
        const amountClass = isWon ? 'text-[var(--light-green)]' : 'text-[var(--accent)]';
        const titleText = isWon ? 'You won' : 'You lost';
        const tagText =
            resolved === 'positive' ? 'Positive news' : resolved === 'negative' ? 'Negative news' : 'Round closed';
        const tagClass =
            resolved === 'positive'
                ? 'border-[var(--light-green)] text-[var(--light-green)]'
                : resolved === 'negative'
                  ? 'border-[var(--soft-pink)] text-[var(--soft-pink)]'
                  : 'border-[var(--coffee-brown)] text-white/80';

        // Derive stats if we have round info
        let winnersPct: number | undefined;
        let losersPct: number | undefined;
        let totalWinnings: number | undefined;
        let totalLosersLost: number | undefined;
        if (round) {
            const pos = round.pot_positive ?? 0;
            const neg = round.pot_negative ?? 0;
            const total = pos + neg;
            if (total > 0) {
                const posPct = Math.round((pos / total) * 100);
                const negPct = 100 - posPct;
                if (resolved === 'positive') {
                    winnersPct = posPct;
                    losersPct = negPct;
                } else if (resolved === 'negative') {
                    winnersPct = negPct;
                    losersPct = posPct;
                }
            }
            if (resolved) {
                // rough estimates: winnings ~ pot of winners; losers lost ~ pot of losers
                totalWinnings = resolved === 'positive' ? pos : neg;
                totalLosersLost = resolved === 'positive' ? neg : pos;
            }
        }

        return {
            titleText,
            amountText,
            amountClass,
            tagText,
            tagClass,
            winnersPct,
            losersPct,
            totalWinnings,
            totalLosersLost,
        };
    }, [bet, round]);

    if (loading) {
        return <div className="pt-8 px-4 txt-footnote text-[var(--charcoal-grey)]">Loading…</div>;
    }
    if (error || !bet) {
        return <div className="pt-8 px-4 txt-footnote text-[var(--soft-pink)]">{error || 'Bet not found'}</div>;
    }

    return (
        <div className="pt-8 px-4 flex flex-col gap-8">
            <div className="flex flex-col gap-4 items-center">
                <div className={`border rounded-[14px] px-4 py-2 txt-footnote ${tagClass}`}>{tagText}</div>
                <p className="txt-title-2 text-center text-white">{titleText}</p>
                <div className="flex items-center gap-2">
                    <Icon name="coins" size={24} />
                    <p className={`txt-title-1 text-center ${amountClass}`}>{amountText}</p>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
                <div className="bg-[#1e1e20] border border-[#2c2c30] rounded-[12px] p-3 flex flex-col items-center gap-2">
                    <p className="txt-body text-[var(--charcoal-grey)] text-center">
                        <span className="text-white">{formatK(totalWinnings)}</span> coins total winnings
                    </p>
                    <div className="h-10 rounded-[14px] border border-[var(--light-green)] bg-[var(--green)] px-3 flex items-center justify-center">
                        <p className="txt-button-bold text-[var(--light-green)]">{winnersPct ?? '—'}%</p>
                    </div>
                    <p className="txt-caption text-[var(--charcoal-grey)] text-center">of players chose this option</p>
                </div>

                <div className="bg-[#1e1e20] border border-[#2c2c30] rounded-[12px] p-3 flex flex-col items-center gap-2">
                    <p className="txt-body text-[var(--charcoal-grey)] text-center">
                        Losers players lost <span className="text-white">{formatK(totalLosersLost)}</span>
                    </p>
                    <div className="h-10 rounded-[14px] border border-[var(--soft-pink)] bg-[var(--red)] px-3 flex items-center justify-center">
                        <p className="txt-button-bold text-[var(--soft-pink)]">{losersPct ?? '—'}%</p>
                    </div>
                    <p className="txt-caption text-[var(--charcoal-grey)] text-center">of players chose this option</p>
                </div>
            </div>
            <ResultCard item={bet} />
        </div>
    );
};
