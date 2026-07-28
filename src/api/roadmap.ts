import { apiClient } from '../services/axios';
import { ApiResponse, RoadmapItem } from '../types';

export const roadmapApi = {
  getRoadmap: async (branch?: string, year?: number): Promise<ApiResponse<RoadmapItem[]>> => {
    const res = await apiClient.get('/roadmaps/', {
      params: { branch, year }
    });
    return res.data;
  },

  toggleMilestone: async (milestoneId: string, isCompleted: boolean): Promise<ApiResponse<RoadmapItem>> => {
    const res = await apiClient.post(`/roadmaps/milestones/${milestoneId}/toggle`, {
      is_completed: isCompleted
    });
    return res.data;
  }
};
