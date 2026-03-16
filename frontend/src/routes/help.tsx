import {createFileRoute} from '@tanstack/react-router';
import {useTranslation} from 'react-i18next';

export const Route = createFileRoute('/help')({
    component: HelpPage,
});

function HelpPage() {
    const {t} = useTranslation();

    return (
        <div className="container py-6">
            {/* Title */}
            <p className="txt-title-2 text-center">{t('help.title')}</p>

            {/* Sections from Figma */}
            <div className="flex flex-col gap-8 mt-6">
                {/* 1. Section */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('help.section1.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('help.section1.item1')}</li>
                        <li className="txt-body">{t('help.section1.item2')}</li>
                    </ul>
                </div>

                {/* 2. Section */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('help.section2.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('help.section2.item1')}</li>
                        <li className="txt-body">{t('help.section2.item2')}</li>
                    </ul>
                </div>

                {/* 3. Rewards */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('help.section3.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('help.section3.item1')}</li>
                        <li className="txt-body">{t('help.section3.item2')}</li>
                        <li className="txt-body">{t('help.section3.item3')}</li>
                    </ul>
                </div>

                {/* 4. Coins */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('help.section4.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('help.section4.item1')}</li>
                        <li className="txt-body">{t('help.section4.item2')}</li>
                    </ul>
                </div>

                {/* 5. Section */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('help.section5.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('help.section5.item1')}</li>
                        <li className="txt-body">{t('help.section5.item2')}</li>
                    </ul>
                </div>

                {/* 6. Referrals */}
                <div className="flex flex-col gap-4">
                    <p className="txt-title-3 text-[var(--accent)]">{t('help.section6.title')}</p>
                    <ul className="list-disc pl-6">
                        <li className="txt-body">{t('help.section6.item1')}</li>
                        <li className="txt-body">{t('help.section6.item2')}</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
