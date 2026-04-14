import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export const getStatus = () => api.get('/status').then(r => r.data);
export const uploadExcel = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data);
};
export const getFilters = () => api.get('/filters').then(r => r.data);
export const getSummary = (sector, type) => api.get('/summary', { params: { sector, type } }).then(r => r.data);
export const getSubcategories = (sector, type) => api.get('/subcategories', { params: { sector, type } }).then(r => r.data);
export const getPivot = (sector, type, subcategories) =>
  api.get('/pivot', { params: { sector, type, subcategories: subcategories?.join(',') || '' } }).then(r => r.data);
export const getRanking = (sector, type) => api.get('/ranking', { params: { sector, type } }).then(r => r.data);
export const getRadar = (sector, type, top = 5) => api.get('/radar', { params: { sector, type, top } }).then(r => r.data);
export const getEvaluators = (sector, type) => api.get('/evaluators', { params: { sector, type } }).then(r => r.data);
export const getHeatmap = (sector, type) => api.get('/heatmap', { params: { sector, type } }).then(r => r.data);
export const exportExcel = () => api.post('/export', null, { responseType: 'blob' }).then(r => {
  const url = window.URL.createObjectURL(r.data);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'Procesamiento_COLDEX_Sectorial_2025.xlsx';
  a.click();
  window.URL.revokeObjectURL(url);
});
