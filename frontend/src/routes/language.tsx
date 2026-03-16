import {createFileRoute} from '@tanstack/react-router';
import {LanguagePage} from '@/features/language';

export const Route = createFileRoute('/language')({
    component: LanguagePage,
});
