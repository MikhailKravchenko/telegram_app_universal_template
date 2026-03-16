import type {CSSProperties} from 'react';

export type WithClassName<T = unknown> = {className?: string} & T;
export type Color = CSSProperties['color'];
