import { studentsApi } from '../api/students';

export const useStudent = () => {
  return {
    getProfile: () => studentsApi.getProfile(),
    updateProfile: (data: any) => studentsApi.updateProfile(data),
    getDashboardSummary: () => studentsApi.getDashboardSummary(),
  };
};
