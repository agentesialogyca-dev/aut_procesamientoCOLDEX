import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { getPivot, getSubcategories } from '../lib/api';
import Card from './Card';
import { Filter, X } from 'lucide-react';

export default function PivotTab({ sector, type }) {
  const [selectedSubcats, setSelectedSubcats] = useState(null);
  const { data: allSubcats } = useApi(() => getSubcategories(sector, type), [sector, type]);
  const { data: pivot, loading } = useApi(
    () => getPivot(sector, type, selectedSubcats),
    [sector, type, selectedSubcats]
  );

  const subcatNames = allSubcats?.map(s => s.name) || [];
  const isFiltered = selectedSubcats && selectedSubcats.length < subcatNames.length;

  const toggleSubcat = (name) => {
    if (!selectedSubcats) {
      setSelectedSubcats(subcatNames.filter(s => s !== name));
    } else if (selectedSubcats.includes(name)) {
      const next = selectedSubcats.filter(s => s !== name);
      setSelectedSubcats(next.length === 0 ? null : next);
    } else {
      setSelectedSubcats([...selectedSubcats, name]);
    }
  };

  const resetFilter = () => setSelectedSubcats(null);

  if (loading) {
    return <div className="bg-card rounded-xl border border-border h-96 animate-pulse" />;
  }

  if (!pivot) return null;

  return (
    <div className="space-y-4">
      {/* Filter chips */}
      <Card>
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-muted flex-shrink-0" />
          <span className="text-xs text-muted font-medium mr-1">Subcategorias:</span>
          {subcatNames.map(name => {
            const active = !selectedSubcats || selectedSubcats.includes(name);
            return (
              <button
                key={name}
                onClick={() => toggleSubcat(name)}
                className={`px-2.5 py-1 rounded-full text-[11px] font-medium transition-all border
                  ${active
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-surface text-muted border-border hover:border-primary-600'
                  }`}
              >
                {name}
              </button>
            );
          })}
          {isFiltered && (
            <button onClick={resetFilter} className="ml-1 text-xs text-primary-600 hover:underline flex items-center gap-0.5">
              <X className="w-3 h-3" /> Limpiar
            </button>
          )}
        </div>
      </Card>

      {/* Pivot Table */}
      <Card title="Calificaciones promedio por empresa y pregunta">
        <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-primary-800">
                <th className="text-left py-2.5 px-3 text-white font-semibold sticky left-0 bg-primary-800 min-w-[280px]">
                  Pregunta
                </th>
                {pivot.companies.map(c => (
                  <th key={c} className="py-2.5 px-2 text-white font-medium text-center min-w-[80px]">
                    <div className="truncate max-w-[90px]" title={c}>{c}</div>
                  </th>
                ))}
                <th className="py-2.5 px-2 text-white font-semibold text-center min-w-[70px] bg-primary-700">Total</th>
              </tr>
            </thead>
            <tbody>
              {pivot.rows.map((row, i) => (
                <PivotRow key={i} row={row} companies={pivot.companies} />
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function PivotRow({ row, companies }) {
  const isL1 = row.level === 1;
  const isL2 = row.level === 2;
  const isL3 = row.level === 3;

  const rowClasses = isL1
    ? 'bg-primary-50 font-bold text-primary-800'
    : isL2
    ? 'bg-blue-50/50 font-semibold text-primary-800'
    : 'hover:bg-surface/50';

  const labelPadding = isL1 ? 'pl-3' : isL2 ? 'pl-7' : 'pl-11';

  return (
    <tr className={`border-b border-border/50 ${rowClasses} transition-colors`}>
      <td className={`py-2 ${labelPadding} pr-3 sticky left-0 ${isL1 ? 'bg-primary-50' : isL2 ? 'bg-blue-50/50' : 'bg-card'}`}>
        {isL1 && <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary-600 mr-2 align-middle" />}
        {isL2 && <span className="inline-block w-1 h-1 rounded-full bg-primary-600/50 mr-2 align-middle" />}
        <span className={isL3 ? 'text-primary-800/80' : ''}>{row.label}</span>
      </td>
      {companies.map(comp => {
        const val = row.values[comp];
        return (
          <td key={comp} className="py-2 px-2 text-center tabular-nums">
            {val != null ? (
              <span className={isL1 || isL2 ? 'font-semibold' : ''}>{val.toFixed(2)}</span>
            ) : (
              <span className="text-subtle">-</span>
            )}
          </td>
        );
      })}
      <td className={`py-2 px-2 text-center font-semibold tabular-nums ${isL1 ? 'bg-primary-100/60' : 'bg-surface/50'}`}>
        {row.total != null ? row.total.toFixed(2) : '-'}
      </td>
    </tr>
  );
}
