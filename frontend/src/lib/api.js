import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

let _cache = null;

const viewKey = (sector, type) => `${sector}|${type}`;
const view = (sector, type) => _cache?.views?.[viewKey(sector, type)] || null;

export const processFile = async (file) => {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/process', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  _cache = data;
  return data;
};

export const hasData = () => _cache !== null;
export const getCurrentFilename = () => _cache?.filename || null;

export const getFilters = () =>
  Promise.resolve(_cache?.filters || { sectors: [], types: [] });

export const getSummary = (sector, type) =>
  Promise.resolve(view(sector, type)?.summary || { empty: true });

export const getSubcategories = (sector, type) =>
  Promise.resolve(view(sector, type)?.subcategories || []);

export const getPivot = (sector, type, subcategories) => {
  const p = view(sector, type)?.pivot || { companies: [], rows: [] };
  if (!subcategories || subcategories.length === 0) return Promise.resolve(p);
  const selected = new Set(subcategories);
  let currentL2Selected = false;
  const filtered = p.rows.filter((row) => {
    if (row.level === 1) return true;
    if (row.level === 2) {
      currentL2Selected = selected.has(row.label);
      return currentL2Selected;
    }
    return currentL2Selected;
  });
  return Promise.resolve({ companies: p.companies, rows: filtered });
};

export const getRanking = (sector, type) =>
  Promise.resolve(view(sector, type)?.ranking || []);

export const getRadar = (sector, type) =>
  Promise.resolve(view(sector, type)?.radar || { companies: [], subcategories: [], data: [] });

export const getEvaluators = (sector, type) =>
  Promise.resolve(view(sector, type)?.evaluators || { counts: [], matrix: { from: [], to: [], values: [] } });

export const getHeatmap = (sector, type) =>
  Promise.resolve(view(sector, type)?.heatmap || { subcategories: [], companies: [], values: [] });

export const exportExcel = async (file) => {
  const form = new FormData();
  form.append('file', file);
  const r = await api.post('/export', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(r.data);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'Procesamiento_COLDEX_Sectorial_2025.xlsx';
  a.click();
  window.URL.revokeObjectURL(url);
};
