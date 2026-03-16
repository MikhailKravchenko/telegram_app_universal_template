/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    theme: {
        extend: {
            fontFamily: {
                'sf-pro-display': ['"SF Pro Display"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
            },
            fontSize: {
                // Typography from Figma design
                'title-1': ['34px', {lineHeight: 'normal', fontWeight: '700'}],
                'title-2': ['26px', {lineHeight: 'normal', fontWeight: '700'}],
                'title-3': ['22px', {lineHeight: 'normal', fontWeight: '590'}],
                headline: ['20px', {lineHeight: 'normal', fontWeight: '590'}],
                subhead: ['17px', {lineHeight: 'normal', fontWeight: '400'}],
                'button-bold': ['16px', {lineHeight: 'normal', fontWeight: '590'}],
                body: ['14px', {lineHeight: 'normal', fontWeight: '400'}],
                footnote: ['13px', {lineHeight: 'normal', fontWeight: '400'}],
                caption: ['11px', {lineHeight: 'normal', fontWeight: '400'}],
            },
            fontWeight: {
                590: '590', // Semibold weight from design
            },
        },
    },
    plugins: [],
};
