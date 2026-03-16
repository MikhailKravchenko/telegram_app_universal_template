import type {FC} from 'react';
import {useTranslation} from 'react-i18next';

type InsufficientBalanceNotificationProps = {
    balance: number;
};

export const InsufficientBalanceNotification: FC<InsufficientBalanceNotificationProps> = ({balance}) => {
    const {t} = useTranslation();

    return (
        <div className="flex gap-5 p-3 pr-10">
            <div className="h-8 w-8 flex items-center justify-center">
                <span className="text-3xl" aria-hidden>
                    💰
                </span>
            </div>
            <div className="flex flex-col gap-2">
                <div className="txt-button-bold">{t('common.insufficientBalance')}</div>
                <div className="txt-body text-[var(--accent)]">
                    {t('common.yourBalance')} {balance}
                </div>
                <div className="txt-body text-[var(--charcoal-grey)]">{t('common.earnMore')}</div>
            </div>
        </div>
    );
};
