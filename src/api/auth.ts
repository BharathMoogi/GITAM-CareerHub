import { apiClient } from '../services/axios';
import { ApiResponse, UserTokenData, StudentProfile } from '../types';

export const authApi = {
  login: async (credentials: { email: string; password: string }): Promise<ApiResponse<UserTokenData>> => {
    const res = await apiClient.post('/auth/login', credentials);
    return res.data;
  },

  getCurrentUser: async (): Promise<ApiResponse<StudentProfile>> => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  refreshToken: async (refreshToken: string): Promise<ApiResponse<UserTokenData>> => {
    const res = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    return res.data;
  },

  logout: async (): Promise<void> => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};
