import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { getGeneralData } from '../lib/api';
import Card from './Card';
import { ChevronDown, ChevronRight, Factory, Store, LayoutGrid, Table as TableIcon, ArrowUp, ArrowDown, ArrowUpDown, Download } from 'lucide-react';

const SECTOR_ICONS = {
  TXT: '🧵', ELT: '⚡', CNS: '🛒', HGR: '🏠', SLD: '💊', SLDI: '🏥',
};

const CSV_ESCAPE = (v) => {
  if (v == null) return '';
  const s = String(v);
  return /[,"\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

function bestScore(comp) {
  const vals = [comp.scores.INDUSTRIAL?.score, comp.scores.CADENA?.score].filter((v) => v != null);
  return vals.length ? Math.max(...vals) : null;
}

function SortHeader({ label, column, sortKey, sortDir, onSort, className = '' }) {
  const active = sortKey === column;
  const Icon = !active ? ArrowUpDown : sortDir === 'asc' ? ArrowUp : ArrowDown;
  return (
    <th
      onClick={() => onSort(column)}
      className={`cursor-pointer select-none py-2 px-3 font-semibold text-primary-800 border-b-2 border-border hover:bg-primary-50/60 ${className}`}
    >
      <div className="inline-flex items-center gap-1">
        {label}
        <Icon className={`w-3 h-3 ${active ? 'text-primary-600' : 'text-subtle'}`} />
      </div>
    </th>
  );
}

export default function GeneralView() {
  const { data, loading } = useApi(() => getGeneralData(), []);
  const [open, setOpen] = useState({});
  const [view, setView] = useState('cards');
  const [sortKey, setSortKey] = useState('sector');
  const [sortDir, setSortDir] = useState('asc');

  if (loading || !data) {
    return <div className="bg-card rounded-xl border border-border h-96 animate-pulse" />;
  }

  const toggle = (code) => setOpen((o) => ({ ...o, [code]: !o[code] }));

  const totalCompanies = data.reduce((s, sec) => s + sec.companies.length, 0);
  const nonEmptySectors = data.filter((s) => s.companies.length > 0);

  const flatRows = data.flatMap((sec) =>
    sec.companies.map((c) => ({ ...c, sector: sec.name, sectorCode: sec.code, best: bestScore(c) }))
  );

  const handleSort = (col) => {
    if (sortKey === col) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(col);
      setSortDir(col === 'score' ? 'desc' : 'asc');
    }
  };

  const sortedRows = [...flatRows].sort((a, b) => {
    let av, bv;
    if (sortKey === 'name') { av = a.name; bv = b.name; }
    else if (sortKey === 'sector') { av = a.sector; bv = b.sector; }
    else if (sortKey === 'score') { av = a.best ?? -Infinity; bv = b.best ?? -Infinity; }
    else { av = 0; bv = 0; }
    const cmp = typeof av === 'string' ? av.localeCompare(bv) : av - bv;
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const downloadCSV = () => {
    const header = ['Sector', 'Empresa', 'Tipo', 'Puntaje IND', 'Rank IND', 'Puntaje CAD', 'Rank CAD', 'Evaluado por', 'Evaluo a'];
    const rows = sortedRows.map((r) => [
      r.sector,
      r.name,
      [r.types.INDUSTRIAL && 'IND', r.types.CADENA && 'CAD'].filter(Boolean).join('/'),
      r.scores.INDUSTRIAL?.score ?? '',
      r.scores.INDUSTRIAL?.rank ?? '',
      r.scores.CADENA?.score ?? '',
      r.scores.CADENA?.rank ?? '',
      r.evaluatedBy.join('; '),
      r.evaluated.join('; '),
    ]);
    const csv = '﻿' + [header, ...rows].map((row) => row.map(CSV_ESCAPE).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'General_COLDEX_Sectorial.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Card>
          <p className="text-xs text-muted font-medium">Sectores con datos</p>
          <p className="text-2xl font-bold text-primary-800 mt-1">{nonEmptySectors.length}</p>
        </Card>
        <Card>
          <p className="text-xs text-muted font-medium">Total empresas evaluadas</p>
          <p className="text-2xl font-bold text-primary-800 mt-1">{totalCompanies}</p>
        </Card>
        <Card>
          <p className="text-xs text-muted font-medium">Promedio empresas/sector</p>
          <p className="text-2xl font-bold text-primary-800 mt-1">
            {nonEmptySectors.length ? (totalCompanies / nonEmptySectors.length).toFixed(1) : '0'}
          </p>
        </Card>
      </div>

      <div className="flex items-center justify-end gap-2">
        {view === 'table' && (
          <button
            onClick={downloadCSV}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-accent text-white hover:brightness-110 transition-all"
          >
            <Download className="w-3.5 h-3.5" /> Descargar CSV
          </button>
        )}
        <div className="inline-flex rounded-lg border border-border bg-card p-0.5">
          <button
            onClick={() => setView('cards')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              view === 'cards' ? 'bg-primary-600 text-white' : 'text-muted hover:text-primary-800'
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" /> Tarjetas
          </button>
          <button
            onClick={() => setView('table')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              view === 'table' ? 'bg-primary-600 text-white' : 'text-muted hover:text-primary-800'
            }`}
          >
            <TableIcon className="w-3.5 h-3.5" /> Tabla
          </button>
        </div>
      </div>

      {view === 'table' && (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-surface/60">
                  <SortHeader label="Sector" column="sector" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} className="text-left min-w-[140px]" />
                  <SortHeader label="Empresa" column="name" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} className="text-left min-w-[180px]" />
                  <th className="text-center py-2 px-3 font-semibold text-primary-800 border-b-2 border-border w-[110px]">Tipo</th>
                  <SortHeader label="Puntaje" column="score" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} className="text-center w-[160px]" />
                  <th className="text-left py-2 px-3 font-semibold text-primary-800 border-b-2 border-border">Evaluado por</th>
                  <th className="text-left py-2 px-3 font-semibold text-primary-800 border-b-2 border-border">Evaluo a</th>
                </tr>
              </thead>
              <tbody>
                {sortedRows.map((r) => (
                  <tr key={`${r.sectorCode}-${r.name}`} className="border-b border-border/50 align-top hover:bg-surface/40">
                    <td className="py-2 px-3">
                      <span className="inline-flex items-center gap-1.5">
                        <span>{SECTOR_ICONS[r.sectorCode]}</span>
                        <span className="text-primary-700 font-medium">{r.sector}</span>
                      </span>
                    </td>
                    <td className="py-2 px-3 font-semibold text-primary-800">{r.name}</td>
                    <td className="py-2 px-3 text-center">
                      <div className="inline-flex gap-1">
                        {r.types.INDUSTRIAL && (
                          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-primary-50 text-primary-700 text-[10px] font-semibold">
                            <Factory className="w-3 h-3" /> IND
                          </span>
                        )}
                        {r.types.CADENA && (
                          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-primary-50 text-primary-700 text-[10px] font-semibold">
                            <Store className="w-3 h-3" /> CAD
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <div className="flex flex-col gap-0.5 items-center">
                        {r.scores.INDUSTRIAL && (
                          <span className="text-[11px]">
                            <span className="text-muted">IND:</span>{' '}
                            <span className="font-bold text-primary-800">{r.scores.INDUSTRIAL.score}</span>
                            <span className="text-subtle"> (#{r.scores.INDUSTRIAL.rank})</span>
                          </span>
                        )}
                        {r.scores.CADENA && (
                          <span className="text-[11px]">
                            <span className="text-muted">CAD:</span>{' '}
                            <span className="font-bold text-primary-800">{r.scores.CADENA.score}</span>
                            <span className="text-subtle"> (#{r.scores.CADENA.rank})</span>
                          </span>
                        )}
                        {!r.scores.INDUSTRIAL && !r.scores.CADENA && (
                          <span className="text-subtle italic">—</span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 px-3 text-muted">
                      {r.evaluatedBy.length ? (
                        <span>
                          <span className="font-semibold text-primary-700">{r.evaluatedBy.length}:</span>{' '}
                          {r.evaluatedBy.join(', ')}
                        </span>
                      ) : (
                        <span className="text-subtle italic">—</span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-muted">
                      {r.evaluated.length ? (
                        <span>
                          <span className="font-semibold text-primary-700">{r.evaluated.length}:</span>{' '}
                          {r.evaluated.join(', ')}
                        </span>
                      ) : (
                        <span className="text-subtle italic">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {view === 'cards' && data.map((sec) => {
        const isOpen = open[sec.code] ?? true;
        const hasData = sec.companies.length > 0;
        return (
          <div key={sec.code} className="bg-card rounded-xl border border-border overflow-hidden">
            <button
              onClick={() => hasData && toggle(sec.code)}
              className={`w-full flex items-center justify-between px-5 py-4 text-left transition-colors ${
                hasData ? 'hover:bg-primary-50/40 cursor-pointer' : 'cursor-default opacity-60'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{SECTOR_ICONS[sec.code] || '📊'}</span>
                <div>
                  <h3 className="font-bold text-primary-800">{sec.name}</h3>
                  <p className="text-xs text-muted">
                    {sec.companies.length} {sec.companies.length === 1 ? 'empresa evaluada' : 'empresas evaluadas'}
                  </p>
                </div>
              </div>
              {hasData && (isOpen ? (
                <ChevronDown className="w-5 h-5 text-muted" />
              ) : (
                <ChevronRight className="w-5 h-5 text-muted" />
              ))}
            </button>

            {isOpen && hasData && (
              <div className="px-5 pb-5">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {sec.companies.map((comp) => (
                    <div key={comp.name} className="border border-border rounded-lg p-3 bg-surface/40">
                      <div className="flex items-center justify-between mb-2 gap-2">
                        <p className="font-semibold text-primary-800 text-sm truncate" title={comp.name}>
                          {comp.name}
                        </p>
                        <div className="flex gap-1 shrink-0">
                          {comp.types.INDUSTRIAL && (
                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-primary-50 text-primary-700 text-[10px] font-semibold">
                              <Factory className="w-3 h-3" /> IND
                            </span>
                          )}
                          {comp.types.CADENA && (
                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-primary-50 text-primary-700 text-[10px] font-semibold">
                              <Store className="w-3 h-3" /> CAD
                            </span>
                          )}
                        </div>
                      </div>

                      {(comp.scores.INDUSTRIAL || comp.scores.CADENA) && (
                        <div className="flex gap-2 mb-2 text-[11px]">
                          {comp.scores.INDUSTRIAL && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-green-light text-primary-800">
                              <span className="text-muted">IND</span>
                              <span className="font-bold">{comp.scores.INDUSTRIAL.score}</span>
                              <span className="text-subtle">#{comp.scores.INDUSTRIAL.rank}</span>
                            </span>
                          )}
                          {comp.scores.CADENA && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-green-light text-primary-800">
                              <span className="text-muted">CAD</span>
                              <span className="font-bold">{comp.scores.CADENA.score}</span>
                              <span className="text-subtle">#{comp.scores.CADENA.rank}</span>
                            </span>
                          )}
                        </div>
                      )}

                      <div className="mb-2">
                        <p className="text-[10px] font-semibold text-primary-600 uppercase tracking-wider mb-1">
                          Evaluado por ({comp.evaluatedBy.length})
                        </p>
                        {comp.evaluatedBy.length ? (
                          <ul className="space-y-0.5">
                            {comp.evaluatedBy.map((name) => (
                              <li key={name} className="text-xs text-muted truncate" title={name}>
                                • {name}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-xs text-subtle italic">—</p>
                        )}
                      </div>

                      <div>
                        <p className="text-[10px] font-semibold text-green/80 uppercase tracking-wider mb-1">
                          Evaluo a ({comp.evaluated.length})
                        </p>
                        {comp.evaluated.length ? (
                          <ul className="space-y-0.5">
                            {comp.evaluated.map((name) => (
                              <li key={name} className="text-xs text-muted truncate" title={name}>
                                • {name}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-xs text-subtle italic">—</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
