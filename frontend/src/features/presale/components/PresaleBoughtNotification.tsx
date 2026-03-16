import type {FC} from 'react';
import {useTranslation} from 'react-i18next';

type PresaleBoughtNotificationProps = {
    amount: number;
};

export const PresaleBoughtNotification: FC<PresaleBoughtNotificationProps> = ({amount}) => {
    const {t} = useTranslation();

    return (
        <div className="flex gap-5 p-3 pr-10">
            <div className="h-8 w-8 flex items-center justify-center">
                <span className="text-3xl" aria-hidden>
                    👀
                </span>
            </div>
            <div className="flex flex-col gap-2">
                <div className="txt-button-bold">
                    {t('presale.youBought')} {amount} {t('common.pulse')}
                </div>
            </div>
        </div>
    );
};
