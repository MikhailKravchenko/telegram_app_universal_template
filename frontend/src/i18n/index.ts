import i18n from 'i18next';
import {initReactI18next} from 'react-i18next';

import en from '@/locales/en.json';
import ru from '@/locales/ru.json';

const STORAGE_KEY = 'app:l10n';

// Determine initial language from localStorage or default to 'en'
const initialLng = ((): 'en' | 'ru' => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored === 'ru' || stored === 'en') return stored;
    } catch {
        /* empty */
    }
    return 'en';
})();

void i18n.use(initReactI18next).init({
    lng: initialLng,
    fallbackLng: 'en',
    resources: {
        en: {translation: en},
        ru: {translation: ru},
    },
    interpolation: {
        escapeValue: false,
    },
    // No language detector, no namespaces
    ns: ['translation'],
    defaultNS: 'translation',
    returnNull: false,
});

export const setAppLanguage = (lng: 'en' | 'ru') => {
    i18n.changeLanguage(lng);
    try {
        localStorage.setItem(STORAGE_KEY, lng);
    } catch {}
};

export default i18n;
