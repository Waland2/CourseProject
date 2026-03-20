import { apiClient } from './client';

const normalizeListResponse = (data) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.districts)) {
    return data.districts;
  }

  if (Array.isArray(data?.ranking)) {
    return data.ranking;
  }

  if (Array.isArray(data?.items)) {
    return data.items;
  }

  return [];
};

export const analyticsApi = {
  getDistrictAnalytics: async (year) => {
    const { data } = await apiClient.get('/analytics/districts/', {
      params: year ? { year } : undefined,
    });
    return normalizeListResponse(data);
  },

  getRanking: async (params) => {
    const { data } = await apiClient.get('/analytics/ranking/', { params });
    return normalizeListResponse(data);
  },

  compareCompanies: async (payload) => {
    const { data } = await apiClient.post('/comparisons/', payload);
    return data;
  },
};