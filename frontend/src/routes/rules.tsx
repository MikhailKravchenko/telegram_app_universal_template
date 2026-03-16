import {createFileRoute} from '@tanstack/react-router';
import {useTranslation} from 'react-i18next';

export const Route = createFileRoute('/rules')({
    component: RulesPage,
});

function RulesPage() {
    const {t} = useTranslation();

    return (
        <div className="container py-6">
            {/* Title */}
            <p className="txt-title-2 text-center">{t('rules.title')}</p>

            {/* Sections from Figma */}
            <div className="flex flex-col gap-8 mt-6">
                {/* 1. Game Currency */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('rules.section1.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('rules.section1.item1')}</li>
                        <li className="txt-body">{t('rules.section1.item2')}</li>
                        <li className="txt-body">{t('rules.section1.item3')}</li>
                    </ul>
                </div>

                {/* 2. Predictions */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('rules.section2.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('rules.section2.item1')}</li>
                        <li className="txt-body">{t('rules.section2.item2')}</li>
                        <li className="txt-body">{t('rules.section2.item3')}</li>
                    </ul>
                </div>

                {/* 3. Rewards */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('rules.section3.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('rules.section3.item1')}</li>
                        <li className="txt-body">{t('rules.section3.item2')}</li>
                        <li className="txt-body">{t('rules.section3.item3')}</li>
                    </ul>
                </div>

                {/* 4. Section */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('rules.section4.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('rules.section4.item1')}</li>
                        <li className="txt-body">{t('rules.section4.item2')}</li>
                        <li className="txt-body">{t('rules.section4.item3')}</li>
                    </ul>
                </div>

                {/* 5. Referrals */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('rules.section5.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('rules.section5.item1')}</li>
                        <li className="txt-body">{t('rules.section5.item2')}</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
