import type {GameRound} from '@/shared/api';

export type BubbleSpec = {
    size: number;
    top: number;
    left: number;
    fill: string;
    border: string;
    anim: any;
    id: number; // unique bubble id
    roundId?: number; // id of betting round (used for API)
};

export type TGame = {
    round: GameRound | null;
    bubbles: BubbleSpec[] | null;
};
