import React from 'react';
import clsx from 'clsx';
import {iconsMap} from '@/assets/icons';
import type {IconProps} from './Icon.types';
import type {WithClassName} from '@/types';
import {getInlineStyle} from '@/shared/lib';
import s from './Icon.module.css';

export const Icon: React.FC<WithClassName<IconProps>> = ({name, fill, stroke, size = 24, className}) => (
    <div
        style={getInlineStyle({style: {}, variables: {fill, stroke, size}})}
        className={clsx(s.icon, {[s.fill]: fill, [s.stroke]: stroke, [s.size]: size}, className)}
    >
        {React.createElement(iconsMap[name])}
    </div>
);
