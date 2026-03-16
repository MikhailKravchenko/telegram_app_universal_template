import {createFileRoute} from '@tanstack/react-router';
import {useTranslation} from 'react-i18next';

const PlaceholderOnePage = () => {
    const {t} = useTranslation();

    return (
        <div className="container py-6 space-y-4">
            <h1 className="txt-title-2 text-center">{t('placeholder1.title')}</h1>
            <p className="txt-body text-center text-[var(--charcoal-grey)]">{t('placeholder1.subtitle')}</p>
        </div>
    );
};

export const Route = createFileRoute('/placeholder-1')({
    component: PlaceholderOnePage,
});

