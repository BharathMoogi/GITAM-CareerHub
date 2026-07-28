import { apiClient } from '../services/axios';
import { ApiResponse, Project } from '../types';

export const projectsApi = {
  getProjects: async (branch?: string, difficulty?: string): Promise<ApiResponse<Project[]>> => {
    const res = await apiClient.get('/projects/', { params: { branch, difficulty } });
    return res.data;
  },

  submitProject: async (projectId: string, githubUrl: string, demoUrl?: string): Promise<ApiResponse<any>> => {
    const res = await apiClient.post(`/projects/${projectId}/submit`, { github_url: githubUrl, demo_url: demoUrl });
    return res.data;
  }
};
