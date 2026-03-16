import axios from 'axios';
import {env} from '@/shared/config';

// Create axios instance with base configuration
export const http = axios.create({
    baseURL: env.API_BASE_URL ? `${env.API_BASE_URL}/api/v1` : 'http://localhost:8000/api/v1',
    timeout: 5000,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for adding auth token
http.interceptors.request.use(
    (config) => {
        return config;
    },
    (error) => {
        return Promise.reject(error);
    },
);

// Response interceptor for handling errors
http.interceptors.response.use(
    (response) => response.data,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized access
            console.error('Unauthorized access');
        }
        return Promise.reject(error);
    },
);
