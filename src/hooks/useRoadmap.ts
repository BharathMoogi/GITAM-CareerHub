import { roadmapApi } from '../api/roadmap';

export const useRoadmap = () => {
  return {
    getRoadmap: (branch?: string, year?: number) => roadmapApi.getRoadmap(branch, year),
    toggleMilestone: (id: string, isCompleted: boolean) => roadmapApi.toggleMilestone(id, isCompleted),
  };
};
