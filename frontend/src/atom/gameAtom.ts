import {atom} from 'jotai/index';
import type {TGame} from '@/types';

export const gameAtom = atom<TGame>({round: null, bubbles: null});
