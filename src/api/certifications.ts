import { apiClient } from '../services/axios';
import { ApiResponse, Certification } from '../types';

export const certificationsApi = {
  getCertifications: async (): Promise<ApiResponse<Certification[]>> => {
    const res = await apiClient.get('/certifications/');
    return res.data;
  },

  claimCertification: async (certId: string, credentialUrl: string): Promise<ApiResponse<any>> => {
    const res = await apiClient.post(`/certifications/${certId}/claim`, { credential_url: credentialUrl });
    return res.data;
  }
};
