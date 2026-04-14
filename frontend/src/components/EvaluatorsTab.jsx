import { useApi } from '../hooks/useApi';
import { getEvaluators } from '../lib/api';
import Card from './Card';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

const PIE_COLORS = [
  '#0052CC', '#36B37E', '#FF8B00', '#6554C0', '#00B8D9',
  '#FF5630', '#FFAB00', '#00875A', '#403294', '#008DA6',
  '#BF2600', '#FF991F', '#006644', '#5243AA', '#00A3BF',
];

function getHeatColor(val) {
  if (val == null) return '#F4F5F7';
  if (val < 2) return '#FFEBE6';
  if (val < 4) return '#FFF0B3';
  if (val < 6) return '#FFFAE6';
  if (val < 8) return '#E3FCEF';
  return '#ABF5D1';
}

export default function EvaluatorsTab({ sector, type }) {
  const { data, loading } = useApi(() => getEvaluators(sector, type), [sector, type]);

  if (loading) return <div className="bg-card rounded-xl border border-border h-96 animate-pulse" />;
  if (!data) return null;

  const { counts, matrix } = data;

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
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #DFE1E6', fontSize: 13 }} />
              <Bar dataKey="count" name="Evaluadores" radius={[0, 6, 6, 0]} barSize={20} fill="#0052CC" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Distribucion">
          <ResponsiveContainer width="100%" height={380}>
            <PieChart>
              <Pie
                data={counts}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={120}
                paddingAngle={2}
                dataKey="count"
                nameKey="company"
                label={({ company, count }) => `${company}: ${count}`}
                labelLine={{ stroke: '#97A0AF', strokeWidth: 1 }}
              >
                {counts.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #DFE1E6', fontSize: 13 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="text-center -mt-2">
            <span className="text-2xl font-bold text-primary-800">
              {counts.reduce((sum, c) => sum + c.count, 0)}
            </span>
            <span className="text-sm text-muted ml-1.5">evaluaciones totales</span>
          </div>
        </Card>
      </div>

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
