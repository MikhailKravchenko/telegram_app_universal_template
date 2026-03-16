import {useTranslation} from 'react-i18next';
import {Icon} from '@/components/Icon';

export const BalanceCard = ({balance}: {balance?: number}) => {
    const {t} = useTranslation();

    return (
        <div
            style={{background: 'linear-gradient(175deg, #000 39.37%, #E45125 99.14%)'}}
            className="w-full rounded-[12px] border border-[var(--coffee-brown)] py-3 px-4 flex flex-col items-center justify-center gap-2"
        >
            <div className="txt-footnote">{t('profile.balance')}</div>
            <div className="flex items-center gap-3">
                <Icon name="coins" size={24} className="text-white" />
                <div className="txt-title-2">{balance ?? 0}</div>
            </div>
        </div>
    );
};
