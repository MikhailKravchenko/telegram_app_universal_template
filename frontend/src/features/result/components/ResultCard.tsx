import type {Bet} from '@/shared/api';
import {Badge} from './Badge';
import {formatTimeAgo} from '../utils/formatTimeAgo';
import {useTranslation} from 'react-i18next';
import {Link} from '@tanstack/react-router';
import {formatNumber} from '@/shared/lib';

const gradientStyle: React.CSSProperties = {
    backgroundImage:
        'linear-gradient(90deg, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.2) 100%), linear-gradient(174deg, rgb(0,0,0) 88%, rgb(228,81,37) 109%)',
};

export const ResultCard = ({item}: {item: Bet}) => {
    const {t} = useTranslation();
    const image = item.news_image_url ?? null;
    const isFinished = item.round_status === 'finished';

    const content = (
        <>
            <div className="flex gap-2 items-center">
                <Badge result={item.round_result} />
                <p>
                    Bets count: {item.bets_count}, Total pot: {formatNumber(item.pot_total)}
                </p>
            </div>
            <div className="w-full">
                <div className="flex flex-col gap-2">
                    <p className="txt-headline text-white">{item.news_title || t('result.newsProcessing')}</p>
                    <p className="txt-footnote text-[var(--charcoal-grey)]">{formatTimeAgo(item.created_at)}</p>
                </div>
            </div>
            {image ? (
                <div className="w-full h-[182px] rounded-[12px] overflow-hidden bg-white">
                    <img src={image} alt="news" className="w-full h-full object-cover" />
                </div>
            ) : null}
            {item.news_content ? <p className="txt-body text-white">{item.news_content}</p> : null}
        </>
    );

    return isFinished ? (
        <Link
            to={`/result/${item.id}`}
            className="border border-[var(--coffee-brown)] rounded-[24px] p-4 flex flex-col gap-4"
            style={gradientStyle}
        >
            {content}
        </Link>
    ) : (
        <div
            className="border border-[var(--coffee-brown)] rounded-[24px] p-4 flex flex-col gap-4"
            style={gradientStyle}
        >
            {content}
        </div>
    );
};
