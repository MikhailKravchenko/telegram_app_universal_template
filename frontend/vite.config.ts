import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import {tanstackRouter} from '@tanstack/router-plugin/vite';
import svgr from 'vite-plugin-svgr';

export default defineConfig({
    server: {
        host: true,
        allowedHosts: true,
    },
    plugins: [
        tanstackRouter({
            target: 'react',
            autoCodeSplitting: true,
        }),
        react(),
        svgr(),
    ],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src'),
        },
    },
});
