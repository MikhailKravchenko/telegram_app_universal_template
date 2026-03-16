import {atom} from 'jotai/index';
import type {TApp} from '@/types/app.ts';

export const appAtom = atom<TApp>({isShowSidebar: false});
