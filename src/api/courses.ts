import { apiClient } from '../services/axios';
import { ApiResponse, Course } from '../types';

export const coursesApi = {
  getCourses: async (branch?: string): Promise<ApiResponse<Course[]>> => {
    const res = await apiClient.get('/courses/', { params: { branch } });
    return res.data;
  },

  enrollCourse: async (courseId: string): Promise<ApiResponse<any>> => {
    const res = await apiClient.post(`/courses/${courseId}/enroll`);
    return res.data;
  },

  updateProgress: async (courseId: string, progressPct: number): Promise<ApiResponse<any>> => {
    const res = await apiClient.patch(`/courses/${courseId}/progress`, { progress_percentage: progressPct });
    return res.data;
  }
};
