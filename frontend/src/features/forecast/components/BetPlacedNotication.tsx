import type {FC} from 'react';
import {useTranslation} from 'react-i18next';

type BetPlacedNotificationProps = {
    sentiment: 'positive' | 'negative';
    amount: number;
    time: string;
};

export const BetPlacedNotification: FC<BetPlacedNotificationProps> = ({sentiment, amount, time}) => {
    const {t} = useTranslation();

    return (
        <div className="flex gap-5 p-3 pr-10">
            <div className="h-8 w-8 flex items-center justify-center">
                <span className="text-3xl" aria-hidden>
                    🎁
                </span>
            </div>
            <div className="flex flex-col gap-2">
                <div className="txt-button-bold">{t('forecast.betPlaced')}</div>
                <div className="txt-body text-[var(--accent)]">
                    {amount} {t('forecast.coinsOn')} {sentiment}
                </div>
                <div className="txt-body text-[var(--white)]">
                    {t('forecast.resultIn')} <span className="text-[var(--accent)]">{time}</span>
                </div>
            </div>
        </div>
    );
};
