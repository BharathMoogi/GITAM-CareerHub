import { apiClient } from '../services/axios';
import { ApiResponse, StudentProfile, DashboardSummary } from '../types';

export const studentsApi = {
  getProfile: async (): Promise<ApiResponse<StudentProfile>> => {
    const res = await apiClient.get('/students/me');
    return res.data;
  },

  updateProfile: async (profileData: Partial<StudentProfile>): Promise<ApiResponse<StudentProfile>> => {
    const res = await apiClient.patch('/students/me', profileData);
    return res.data;
  },

  getDashboardSummary: async (): Promise<ApiResponse<DashboardSummary>> => {
    const res = await apiClient.get('/dashboard/summary');
    return res.data;
  },

  getReadinessDetails: async (): Promise<ApiResponse<any>> => {
    const res = await apiClient.get('/dashboard/readiness');
    return res.data;
  }
};
