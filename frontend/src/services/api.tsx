// src/services/api.ts
import axios from 'axios';
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes for AI/LLM requests that may take longer
  // Prevent axios from following redirects automatically (causes auth header loss)
  maxRedirects: 0,
  validateStatus: (status) => status >= 200 && status < 400,
});

// Request interceptor - Add auth token to requests
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('meditrack_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle network errors (no response received)
    if (!error.response) {
      const networkError = new Error(
        error.code === 'ECONNABORTED'
          ? 'Request timeout. The server is taking too long to respond. Please check your internet connection.'
          : 'Unable to connect to server. Please check your internet connection and try again.'
      );
      networkError.name = 'NetworkError';
      return Promise.reject(networkError);
    }

    // Handle authentication errors
    if (error.response.status === 401) {
      // Prevent infinite redirect loops
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        localStorage.removeItem('meditrack_token');
        // Use replace to prevent back-button issues
        window.location.replace('/login');
      }
      // Return a never-resolving promise to stop the chain and prevent retries
      return new Promise(() => {});
    }

    // Handle other HTTP errors
    const errorData = error.response.data as { detail?: string; message?: string } | undefined;
    const message = errorData?.detail || errorData?.message ||
      `Server error (${error.response.status}): ${error.response.statusText}`;

    const apiError = new Error(message);
    apiError.name = 'APIError';
    return Promise.reject(apiError);
  }
);

export default api;