import { apiClient } from './client';

const normalizeListResponse = (data) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.history)) {
    return data.history;
  }

  if (Array.isArray(data?.items)) {
    return data.items;
  }

  return [];
};

export const companiesApi = {
  getCompanies: async (params = {}) => {
    const { data } = await apiClient.get('/managing-companies/', { params });
    return data;
  },

  getSuggestions: async (query) => {
    if (!query || !query.trim()) {
      return [];
    }

    const { data } = await apiClient.get('/managing-companies/suggestions/', {
      params: { query: query.trim() },
    });

    return normalizeListResponse(data);
  },

  getCompanyById: async (id, year) => {
    const { data } = await apiClient.get(`/managing-companies/${id}/`, {
      params: year ? { year } : {},
    });

    return data;
  },

  getCompanyHistory: async (id) => {
    const { data } = await apiClient.get(`/managing-companies/${id}/history/`);
    return normalizeListResponse(data);
  },

  getSimilarCompanies: async (id, params = {}) => {
    const { data } = await apiClient.get(`/managing-companies/${id}/similar/`, {
      params,
    });

    return normalizeListResponse(data);
  },

  getBenchmark: async (id, year) => {
    const { data } = await apiClient.get(`/managing-companies/${id}/benchmark/`, {
      params: year ? { year } : {},
    });

    return data;
  },

  getInsights: async (id, year) => {
    const { data } = await apiClient.get(`/managing-companies/${id}/insights/`, {
      params: year ? { year } : {},
    });

    return data;
  },
};