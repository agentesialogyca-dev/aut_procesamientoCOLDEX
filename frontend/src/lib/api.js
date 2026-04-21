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

export const getGeneralData = () => {
  if (!_cache) return Promise.resolve([]);
  const sectors = _cache.filters.sectors;
  const types = _cache.filters.types;
  const result = sectors.map((s) => {
    const combined = {};
    const ensure = (name) => {
      if (!combined[name]) combined[name] = { evaluatedBy: {}, evaluated: {}, types: {}, scores: {} };
      return combined[name];
    };

    for (const t of types) {
      const v = _cache.views[`${s.code}|${t.code}`];
      if (!v || v.summary?.empty) continue;
      const { matrix } = v.evaluators;
      const rankingMap = Object.fromEntries((v.ranking || []).map((r) => [r.company, r]));

      matrix.to.forEach((toName, ci) => {
        const evaluators = matrix.from.filter((_, ri) => matrix.values[ri]?.[ci] != null);
        const c = ensure(toName);
        c.evaluatedBy[t.code] = evaluators;
        c.types[t.code] = true;
        const r = rankingMap[toName];
        if (r) c.scores[t.code] = { score: r.score, rank: r.rank };
      });

      matrix.from.forEach((fromName, ri) => {
        const targets = matrix.to.filter((_, ci) => matrix.values[ri]?.[ci] != null);
        const c = ensure(fromName);
        c.evaluated[t.code] = targets;
      });
    }

    const companies = Object.entries(combined)
      .map(([name, c]) => {
        const allBy = new Set();
        Object.values(c.evaluatedBy).forEach((list) => list.forEach((n) => allBy.add(n)));
        const allEvaluated = new Set();
        Object.values(c.evaluated).forEach((list) => list.forEach((n) => allEvaluated.add(n)));
        return {
          name,
          types: c.types,
          scores: c.scores,
          evaluatedBy: [...allBy].sort(),
          evaluated: [...allEvaluated].sort(),
        };
      })
      .sort((a, b) => a.name.localeCompare(b.name));

    return { code: s.code, name: s.name, companies };
  });
  return Promise.resolve(result);
};

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
  a.download = 'Procesamiento_LOGYCA_COLDEX_Sectorial.xlsx';
  a.click();
  window.URL.revokeObjectURL(url);
};
