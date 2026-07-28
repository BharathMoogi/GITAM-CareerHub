import { projectsApi } from '../api/projects';

export const useProjects = () => {
  return {
    getProjects: (branch?: string, difficulty?: string) => projectsApi.getProjects(branch, difficulty),
    submitProject: (id: string, githubUrl: string, demoUrl?: string) => projectsApi.submitProject(id, githubUrl, demoUrl),
  };
};
