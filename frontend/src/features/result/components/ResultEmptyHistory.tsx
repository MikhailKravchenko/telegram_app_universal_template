import {useTranslation} from 'react-i18next';

export const ResultEmptyHistory = () => {
    const {t} = useTranslation();

    return (
        <div className="flex flex-col items-center justify-center h-full">
            <div className="flex flex-col gap-2 w-[280px]">
                <p className="txt-title-2 text-center text-[var(--accent)]">{t('result.emptyTitle')}</p>
                <p className="txt-body text-center text-[var(--white)]">{t('result.emptyDescription')}</p>
            </div>
        </div>
    );
};
