import { coursesApi } from '../api/courses';

export const useCourses = () => {
  return {
    getCourses: (branch?: string) => coursesApi.getCourses(branch),
    enrollCourse: (courseId: string) => coursesApi.enrollCourse(courseId),
    updateProgress: (courseId: string, progressPct: number) => coursesApi.updateProgress(courseId, progressPct),
  };
};
