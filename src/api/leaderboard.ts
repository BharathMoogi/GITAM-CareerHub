import { apiClient } from '../services/axios';
import { ApiResponse } from '../types';

export const leaderboardApi = {
  getLeaderboard: async (department?: string): Promise<ApiResponse<any>> => {
    const res = await apiClient.get('/gamification/leaderboard', { params: { department } });
    return res.data;
  },

  getXpStatus: async (): Promise<ApiResponse<any>> => {
    const res = await apiClient.get('/gamification/xp');
    return res.data;
  }
};
