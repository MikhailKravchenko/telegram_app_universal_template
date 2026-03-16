import {atom} from 'jotai';
import type {TUser} from '@/types/user';

export const userAtom = atom<TUser | null>(null);
