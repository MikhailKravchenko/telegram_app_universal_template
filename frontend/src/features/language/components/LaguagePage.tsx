import {useTranslation} from 'react-i18next';
import {useState} from 'react';
import type {LanguageCode} from '@/shared/ui';
import i18n, {setAppLanguage} from '@/i18n';
import {LanguageRow} from './LanguageRow';

type SupportedLanguage = 'en' | 'ru';

const languages: Array<{
    code: LanguageCode;
    name: string;
    translationKey: string;
}> = [
    {code: 'en', name: 'English (US)', translationKey: 'english'},
    {code: 'ru', name: 'Русский', translationKey: 'russian'},
];

export const LanguagePage = () => {
    const {t} = useTranslation();
    const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>(
        (i18n.language as SupportedLanguage) === 'ru' ? 'ru' : 'en',
    );

    const handleLanguageSelect = (languageCode: LanguageCode) => {
        setSelectedLanguage(languageCode);
        setAppLanguage(languageCode as SupportedLanguage);
    };

    return (
        <div className="flex flex-col items-center gap-8">
            {/* Title */}
            <h1 className="txt-title-2 text-center text-white w-full">{t('language.title')}</h1>

            {/* Language List */}
            <div className="flex flex-col w-full">
                {languages.map((language) => (
                    <LanguageRow
                        key={language.code}
                        language={language}
                        isSelected={selectedLanguage === language.code}
                        onSelect={() => handleLanguageSelect(language.code)}
                    />
                ))}
            </div>
        </div>
    );
};
