import type {CSSProperties} from 'react';

export interface ICssVariable {
    [key: string]: string | number | undefined;
}

/**
 * @param {CssVariableProps} variables - object which contains **key** as a name of a variable and a value
 * @returns property like object
 * @example const style = cssVariable({x: 100})
 *          //style = {'--x': 100}
 */
export const cssVariable = (variables: ICssVariable) => {
    const newVariables = {} as ICssVariable;
    Object.entries(variables).forEach(([property, value]) => {
        if (value) {
            newVariables[`--${property}`] = value;
        }
    });
    return newVariables as CSSProperties;
};
