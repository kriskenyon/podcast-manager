import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Podcasts API
export const podcasts = {
  getAll: (params = {}) => api.get('/podcasts', { params }),
  getById: (id) => api.get(`/podcasts/${id}`),
  getWithEpisodes: (id) => api.get(`/podcasts/${id}/with-episodes`),
  create: (data) => api.post('/podcasts', data),
  update: (id, data) => api.put(`/podcasts/${id}`, data),
  delete: (id) => api.delete(`/podcasts/${id}`),
  refresh: (id) => api.post(`/podcasts/${id}/refresh`),
}

// Episodes API
export const episodes = {
  getByPodcast: (podcastId, params = {}) =>
    api.get(`/podcasts/${podcastId}/episodes`, { params }),
  getById: (id) => api.get(`/episodes/${id}`),
}

// Downloads API
export const downloads = {
  getAll: (params = {}) => api.get('/downloads', { params }),
  getById: (id) => api.get(`/downloads/${id}`),
  queue: (episodeId) => api.post(`/episodes/${episodeId}/download`),
  delete: (id, deleteFile = true) =>
    api.delete(`/downloads/${id}`, { params: { delete_file: deleteFile } }),
  processQueue: () => api.post('/downloads/process-queue'),
  retryFailed: () => api.post('/downloads/retry-failed'),
}

// Jobs API
export const jobs = {
  getAll: () => api.get('/jobs'),
  trigger: (jobId) => api.post(`/jobs/${jobId}/trigger`),
  pause: (jobId) => api.post(`/jobs/${jobId}/pause`),
  resume: (jobId) => api.post(`/jobs/${jobId}/resume`),
}

// Health Check
export const health = {
  check: () => api.get('/health'),
}

export default api
