import { internshipsApi } from '../api/internships';

export const useInternships = () => {
  return {
    getInternships: () => internshipsApi.getInternships(),
    applyInternship: (id: string) => internshipsApi.applyInternship(id),
  };
};
