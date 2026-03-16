import {createFileRoute} from '@tanstack/react-router';
import {ResultPage} from '@/features/result';

export const Route = createFileRoute('/result/')({
    component: ResultPage,
});
