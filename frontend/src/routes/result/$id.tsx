import {createFileRoute} from '@tanstack/react-router';
import {ResultDetailsPage} from '@/features/result';

export const Route = createFileRoute('/result/$id')({
    component: ResultDetailsPage,
});
