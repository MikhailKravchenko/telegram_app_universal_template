import type {BubbleSpec} from '@/types';
import {randomInt} from '@/shared/lib';
import {BUBBLE_COLORS} from '../colors';

export const createBubbleSpec = (viewportW: number, viewportH: number, id: number, roundId?: number): BubbleSpec => {
    const size = randomInt(44, 76);
    const padding = 8;
    const maxLeft = Math.max(padding, viewportW - size - padding);
    const maxTop = Math.max(padding, viewportH - size - padding);
    const left = randomInt(padding, maxLeft);
    const top = randomInt(padding, maxTop);
    const c = BUBBLE_COLORS[randomInt(0, BUBBLE_COLORS.length - 1)];
    return {size, top, left, fill: c.fill, border: c.border, anim: c.anim, id, roundId};
};
