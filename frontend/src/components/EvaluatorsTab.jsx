import { useApi } from '../hooks/useApi';
import { getEvaluators } from '../lib/api';
import Card from './Card';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList,
} from 'recharts';

function getHeatColor(val) {
  if (val == null) return '#F4F5F7';
  if (val < 2) return '#FFEBE6';
  if (val < 4) return '#FFF0B3';
  if (val < 6) return '#FFFAE6';
  if (val < 8) return '#E3FCEF';
  return '#ABF5D1';
}

function EvaluatorTooltip({ active, payload, evaluatorsByCompany }) {
  if (!active || !payload || !payload.length) return null;
  const row = payload[0].payload;
  const names = evaluatorsByCompany[row.company] || [];
  return (
    <div className="bg-white rounded-lg border border-border shadow-lg px-3 py-2 text-xs max-w-[240px]">
      <p className="font-semibold text-primary-800 mb-1">{row.company}</p>
      <p className="text-muted mb-1.5">{row.count} {row.count === 1 ? 'evaluador' : 'evaluadores'}</p>
      <ul className="space-y-0.5">
        {names.map(n => (
          <li key={n} className="text-primary-700">• {n}</li>
        ))}
      </ul>
    </div>
  );
}

export default function EvaluatorsTab({ sector, type }) {
  const { data, loading } = useApi(() => getEvaluators(sector, type), [sector, type]);

  if (loading) return <div className="bg-card rounded-xl border border-border h-96 animate-pulse" />;
  if (!data) return null;

  const { counts, matrix } = data;

  const evaluatorsByCompany = Object.fromEntries(
    matrix.to.map((toName, ci) => [
      toName,
      matrix.from.filter((_, ri) => matrix.values[ri]?.[ci] != null),
    ])
  );

  // Histograma: cuantas empresas tuvieron N evaluadores
  const histogramMap = counts.reduce((acc, { count }) => {
    acc[count] = (acc[count] || 0) + 1;
    return acc;
  }, {});
  const histogramData = Object.entries(histogramMap)
    .map(([bucket, companies]) => ({ bucket: Number(bucket), companies }))
    .sort((a, b) => a.bucket - b.bucket);

  const totalEvaluations = counts.reduce((sum, c) => sum + c.count, 0);
  const avgEvaluators = counts.length ? (totalEvaluations / counts.length).toFixed(1) : '0';
  const maxEvaluators = counts.length ? Math.max(...counts.map(c => c.count)) : 0;
  const minEvaluators = counts.length ? Math.min(...counts.map(c => c.count)) : 0;

  return (
    <div className="space-y-5">
      {/* Cards + Pie */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card title="Evaluadores por empresa">
          <ResponsiveContainer width="100%" height={Math.max(300, counts.length * 32)}>
            <BarChart data={[...counts].reverse()} layout="vertical" margin={{ left: 10, right: 30, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#6B778C' }} axisLine={false} />
              <YAxis dataKey="company" type="category" width={150} tick={{ fontSize: 11, fill: '#172B4D' }} axisLine={false} tickLine={false} />
              <Tooltip content={<EvaluatorTooltip evaluatorsByCompany={evaluatorsByCompany} />} cursor={{ fill: '#F4F5F7' }} />
              <Bar dataKey="count" name="Evaluadores" radius={[0, 6, 6, 0]} barSize={20} fill="#0052CC" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Distribucion de evaluadores">
          <div className="grid grid-cols-4 gap-2 mb-4">
            <div className="rounded-lg bg-primary-50 px-3 py-2">
              <p className="text-[10px] font-semibold text-primary-600 uppercase tracking-wider">Empresas</p>
              <p className="text-xl font-bold text-primary-800">{counts.length}</p>
            </div>
            <div className="rounded-lg bg-primary-50 px-3 py-2">
              <p className="text-[10px] font-semibold text-primary-600 uppercase tracking-wider">Promedio</p>
              <p className="text-xl font-bold text-primary-800">{avgEvaluators}</p>
            </div>
            <div className="rounded-lg bg-primary-50 px-3 py-2">
              <p className="text-[10px] font-semibold text-primary-600 uppercase tracking-wider">Min</p>
              <p className="text-xl font-bold text-primary-800">{minEvaluators}</p>
            </div>
            <div className="rounded-lg bg-primary-50 px-3 py-2">
              <p className="text-[10px] font-semibold text-primary-600 uppercase tracking-wider">Max</p>
              <p className="text-xl font-bold text-primary-800">{maxEvaluators}</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={histogramData} margin={{ top: 20, right: 20, bottom: 28, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" vertical={false} />
              <XAxis
                dataKey="bucket"
                tick={{ fontSize: 11, fill: '#6B778C' }}
                axisLine={false}
                label={{ value: 'Numero de evaluadores', position: 'insideBottom', offset: -14, style: { fontSize: 11, fill: '#6B778C' } }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#6B778C' }}
                axisLine={false}
                allowDecimals={false}
                label={{ value: 'Empresas', angle: -90, position: 'insideLeft', style: { fontSize: 11, fill: '#6B778C', textAnchor: 'middle' } }}
              />
              <Tooltip
                cursor={{ fill: '#F4F5F7' }}
                contentStyle={{ borderRadius: 10, border: '1px solid #DFE1E6', fontSize: 13 }}
                formatter={(value) => [`${value} ${value === 1 ? 'empresa' : 'empresas'}`, '']}
                labelFormatter={(v) => `${v} ${v === 1 ? 'evaluador' : 'evaluadores'}`}
              />
              <Bar dataKey="companies" fill="#0052CC" radius={[6, 6, 0, 0]} barSize={36}>
                <LabelList dataKey="companies" position="top" style={{ fontSize: 11, fontWeight: 600, fill: '#0052CC' }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <p className="text-center text-xs text-muted mt-2">
            <span className="font-bold text-primary-800">{totalEvaluations}</span> evaluaciones totales
          </p>
        </Card>
      </div>

      {/* Lista quien evaluo a quien */}
      <Card title="Quien evaluo a cada empresa">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {counts.map(({ company, count }) => (
            <div key={company} className="border border-border rounded-lg p-3 bg-surface/40">
              <div className="flex items-center justify-between mb-2">
                <p className="font-semibold text-primary-800 text-sm truncate" title={company}>{company}</p>
                <span className="inline-flex items-center justify-center min-w-[22px] h-[22px] rounded-full bg-primary-600 text-white text-[11px] font-bold px-1.5">
                  {count}
                </span>
              </div>
              <ul className="space-y-0.5">
                {(evaluatorsByCompany[company] || []).map(name => (
                  <li key={name} className="text-xs text-muted truncate" title={name}>
                    • {name}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Card>

      {/* Matrix */}
      <Card title="Matriz de evaluacion (Evaluador x Evaluado)">
        <div className="overflow-x-auto">
          <table className="w-full text-[11px] border-collapse">
            <thead>
              <tr>
                <th className="text-left py-2 px-2 font-semibold text-primary-800 bg-surface sticky left-0 min-w-[140px] border-b-2 border-border">
                  Evaluador / Evaluado
                </th>
                {matrix.to.map(c => (
                  <th key={c} className="py-2 px-1.5 font-medium text-muted text-center min-w-[65px] bg-surface border-b-2 border-border">
                    <div className="truncate max-w-[70px] mx-auto" title={c}>{c}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.from.map((from, ri) => (
                <tr key={from} className="border-b border-border/30">
                  <td className="py-1.5 px-2 font-medium text-primary-800 sticky left-0 bg-card">{from}</td>
                  {matrix.values[ri].map((val, ci) => (
                    <td key={ci} className="py-1 px-1 text-center">
                      {val != null ? (
                        <div
                          className="rounded py-0.5 font-semibold mx-auto"
                          style={{ backgroundColor: getHeatColor(val), minWidth: 40 }}
                        >
                          {val.toFixed(1)}
                        </div>
                      ) : (
                        <span className="text-subtle/40">-</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
