import { placementsApi } from '../api/placements';

export const usePlacements = () => {
  return {
    getDrives: () => placementsApi.getDrives(),
    getPlacementStats: () => placementsApi.getPlacementStats(),
  };
};
