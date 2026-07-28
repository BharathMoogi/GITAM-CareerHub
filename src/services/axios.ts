/* ==========================================================================
   GITAM CareerHub — Central Axios Service Configuration
   Includes JWT Interceptor, Token Refresh, and Error Handler
   ========================================================================== */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = (typeof window !== 'undefined' && (window as any).API_BASE_URL)
  || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 15000,
});

/* Request Interceptor: Attach JWT Bearer Token */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

/* Response Interceptor: Error Handling & Refresh Logic */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const refreshRes = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          if (refreshRes.data && refreshRes.data.data?.access_token) {
            const newToken = refreshRes.data.data.access_token;
            localStorage.setItem('access_token', newToken);
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return apiClient(originalRequest);
          }
        }
      } catch (refreshErr) {
        console.error('Session expired. Redirecting to login...', refreshErr);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    }

    return Promise.reject(error);
  }
);
