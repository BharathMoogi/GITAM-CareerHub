import { certificationsApi } from '../api/certifications';

export const useCertifications = () => {
  return {
    getCertifications: () => certificationsApi.getCertifications(),
    claimCertification: (id: string, url: string) => certificationsApi.claimCertification(id, url),
  };
};
