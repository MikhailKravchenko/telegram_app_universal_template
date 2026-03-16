import {createFileRoute} from '@tanstack/react-router';
import {PresalePage} from '@/features/presale';

export const Route = createFileRoute('/presale')({
    component: PresalePage,
});
