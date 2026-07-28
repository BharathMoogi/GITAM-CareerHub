import { apiClient } from '../services/axios';
import { ApiResponse, PlacementDrive } from '../types';

export const placementsApi = {
  getDrives: async (): Promise<ApiResponse<PlacementDrive[]>> => {
    const res = await apiClient.get('/placement/drives');
    return res.data;
  },

  getPlacementStats: async (): Promise<ApiResponse<any>> => {
    const res = await apiClient.get('/placement/stats');
    return res.data;
  }
};
