/// <reference types="vite/client" />

declare module '*.svg' {
    import React from 'react';
    const ReactComponent: React.FunctionComponent<React.SVGProps<SVGSVGElement> & {className?: string}>;
    export default ReactComponent;
}

declare module '*.svg?react' {
    import React from 'react';
    const ReactComponent: React.FunctionComponent<React.SVGProps<SVGSVGElement> & {className?: string}>;
    export default ReactComponent;
}
