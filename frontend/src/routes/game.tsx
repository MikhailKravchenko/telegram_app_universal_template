import {createFileRoute} from '@tanstack/react-router';
import {BubbleGame} from '@/features/bubble-game';

const Game = () => <BubbleGame />;

export const Route = createFileRoute('/game')({
    component: Game,
});
