import {useTranslation} from 'react-i18next';

export const Badge = ({result}: {result?: string | null}) => {
    const {t} = useTranslation();
    const isPositive = result === 'positive';
    const isNegative = result === 'negative';

    const classes = isPositive
        ? 'bg-[var(--green)] border-[var(--light-green)] text-[var(--light-green)]'
        : isNegative
          ? 'bg-[var(--red)] border-[var(--soft-pink)] text-[var(--soft-pink)]'
          : 'bg-[rgba(255,255,255,0.06)] border-[var(--coffee-brown)] text-white/80';

    const label = isPositive ? t('result.positive') : isNegative ? t('result.negative') : t('result.closed');

    return (
        <div
            className={`inline-flex items-center justify-center px-4 py-2 rounded-[12px] border txt-button-bold ${classes}`}
        >
            {label}
        </div>
    );
};
