import { apiClient } from '../services/axios';
import { ApiResponse, Internship } from '../types';

export const internshipsApi = {
  getInternships: async (): Promise<ApiResponse<Internship[]>> => {
    const res = await apiClient.get('/internships/');
    return res.data;
  },

  applyInternship: async (internshipId: string): Promise<ApiResponse<any>> => {
    const res = await apiClient.post(`/internships/${internshipId}/apply`);
    return res.data;
  }
};
