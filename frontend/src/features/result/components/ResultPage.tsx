import {useEffect, useRef, useState} from 'react';
import {getBets, type Bet} from '@/shared/api';
import {ResultCard} from './ResultCard';
import {ResultEmptyHistory} from './ResultEmptyHistory';
import {useTranslation} from 'react-i18next';

export const ResultPage = () => {
    const {t} = useTranslation();
    const [items, setItems] = useState<Bet[]>([]);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [done, setDone] = useState(false);
    const loadedPagesRef = useRef<Set<number>>(new Set());

    const fetchPage = async () => {
        if (loading || done || loadedPagesRef.current.has(page)) return;
        loadedPagesRef.current.add(page);
        setLoading(true);
        try {
            const res = await getBets({
                page,
            });
            const newItems = res.results;
            setItems((prev) => {
                return [...prev, ...newItems];
            });
            // decide next step
            const nextPage = page + 1;
            if (res.next && nextPage <= (res.total_pages || 0)) {
                setPage(nextPage);
            } else {
                setDone(true);
            }
        } catch (e) {
            console.error('Failed to load results', e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPage();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Infinite scroll observer
    const sentinelRef = useRef<HTMLDivElement | null>(null);
    useEffect(() => {
        const el = sentinelRef.current;
        if (!el) return;
        const obs = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting && !loading && !done && items.length > 0) {
                        fetchPage();
                    }
                });
            },
            {root: null, rootMargin: '100px', threshold: 0},
        );
        obs.observe(el);
        return () => obs.disconnect();
    }, [loading, done]);

    if (!loading && items.length === 0 && done) {
        return <ResultEmptyHistory />;
    }

    return (
        <div className="pt-8 px-4 gap-4 flex flex-col">
            <p className="txt-title-2 text-center text-white">{t('result.title')}</p>

            <div className="flex flex-col gap-3">
                {items.map((it) => (
                    <ResultCard key={it.id} item={it} />
                ))}
            </div>
            {loading ? (
                <div className="text-center txt-footnote text-[var(--charcoal-grey)] py-4">{t('common.loading')}</div>
            ) : null}
            {/* Sentinel for infinite loading */}
            <div ref={sentinelRef} className="h-1" />
        </div>
    );
};
