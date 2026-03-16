import type {CSSProperties} from 'react';
import {cssVariable} from './cssVariable';
import type {ICssVariable} from './cssVariable';

export interface GetInlineStyleProperties {
    style?: CSSProperties;
    variables?: ICssVariable;
}

/**
 * @param {CSSProperties} style - inline styles,
 * @param {ICssVariable} variables - object which contains **key** as a name of a variable and a value,
 * @returns inline style object
 */
export const getInlineStyle = ({style = {}, variables = {}}: GetInlineStyleProperties) =>
    ({...style, ...cssVariable(variables)}) as CSSProperties;
