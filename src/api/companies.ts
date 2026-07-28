import { apiClient } from '../services/axios';
import { ApiResponse, Company } from '../types';

export const companiesApi = {
  getCompanies: async (): Promise<ApiResponse<Company[]>> => {
    const res = await apiClient.get('/companies/');
    return res.data;
  },

  getCompanyReadiness: async (companyId: string): Promise<ApiResponse<any>> => {
    const res = await apiClient.get(`/companies/${companyId}/readiness`);
    return res.data;
  }
};
