import { companiesApi } from '../api/companies';

export const useCompanies = () => {
  return {
    getCompanies: () => companiesApi.getCompanies(),
    getCompanyReadiness: (id: string) => companiesApi.getCompanyReadiness(id),
  };
};
