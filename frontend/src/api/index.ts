import api from './axios';

export const AuthService = {
  getDemoToken: async (role: 'ADMIN' | 'ANALYST') => {
    const response = await api.post('/api/auth/demo-token/', { role });
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    localStorage.setItem('user', JSON.stringify(response.data.user));
    return response.data;
  },
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }
};

export const IngestionService = {
  getDataSources: async () => {
    const response = await api.get('/api/ingestion/data-sources/');
    return response.data;
  },
  uploadFile: async (file: File, dataSourceId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('data_source_id', dataSourceId);
    
    const response = await api.post('/api/ingestion/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },
  getBatches: async () => {
    const response = await api.get('/api/ingestion/batches/');
    return response.data;
  }
};

export const RecordsService = {
  getRecords: async (params?: any) => {
    const response = await api.get('/api/records/', { params });
    return response.data;
  },
  approveRecord: async (id: string) => {
    const response = await api.post(`/api/records/${id}/approve/`);
    return response.data;
  },
  flagRecord: async (id: string, reason: string) => {
    const response = await api.post(`/api/records/${id}/flag/`, { reason });
    return response.data;
  },
  rejectRecord: async (id: string, reason: string) => {
    const response = await api.post(`/api/records/${id}/reject/`, { reason });
    return response.data;
  },
  getDashboardStats: async () => {
    const response = await api.get('/api/dashboard/stats/');
    return response.data;
  }
};
