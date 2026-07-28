import { apiClient } from '../services/axios';
import { ApiResponse, AIChatMessage } from '../types';

export const aiApi = {
  sendMessage: async (prompt: string, context?: any): Promise<ApiResponse<AIChatMessage>> => {
    const res = await apiClient.post('/ai/chat', { prompt, context });
    return res.data;
  },

  getRecommendation: async (): Promise<ApiResponse<any>> => {
    const res = await apiClient.get('/ai/recommendation');
    return res.data;
  }
};
