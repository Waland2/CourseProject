import { apiClient } from './client';

export const referenceApi = {
  getYears: async () => {
    const { data } = await apiClient.get('/reference/years/');
    return data;
  },
  getAdmAreas: async () => {
    const { data } = await apiClient.get('/reference/adm-areas/');
    return data;
  },
};
