import type {Color} from '@/types';
import type {TIconMapKeys} from '@/assets/icons';

export type IconProps = {
    name: TIconMapKeys;
    fill?: Color;
    stroke?: Color;
    size?: number;
};
