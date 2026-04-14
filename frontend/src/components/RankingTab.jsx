import { useApi } from '../hooks/useApi';
import { getRanking, getRadar } from '../lib/api';
import Card from './Card';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
} from 'recharts';

const RADAR_COLORS = ['#0052CC', '#36B37E', '#FF8B00', '#6554C0', '#00B8D9'];

function RankBadge({ rank }) {
  if (rank === 1) return <div className="w-7 h-7 rounded-full bg-amber-400 text-amber-900 flex items-center justify-center text-xs font-black">1</div>;
  if (rank === 2) return <div className="w-7 h-7 rounded-full bg-gray-300 text-gray-700 flex items-center justify-center text-xs font-black">2</div>;
  if (rank === 3) return <div className="w-7 h-7 rounded-full bg-orange-400 text-orange-900 flex items-center justify-center text-xs font-black">3</div>;
  return <div className="w-7 h-7 rounded-full bg-surface text-muted flex items-center justify-center text-xs font-bold">{rank}</div>;
}

export default function RankingTab({ sector, type }) {
  const { data: ranking, loading: l1 } = useApi(() => getRanking(sector, type), [sector, type]);
  const { data: radar, loading: l2 } = useApi(() => getRadar(sector, type, 5), [sector, type]);

  if (l1 || l2) return <div className="bg-card rounded-xl border border-border h-96 animate-pulse" />;
  if (!ranking?.length) return <p className="text-muted text-center py-12">Sin datos suficientes</p>;

  const top7 = Math.min(7, ranking.length);
  const chartData = [...ranking].reverse().slice(0, 15);

  // Radar data
  const radarData = radar?.subcategories?.map((sub, i) => {
    const entry = { subcategory: sub };
    radar.data.forEach(d => { entry[d.company] = d.values[i]; });
    return entry;
  }) || [];

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Chart */}
        <Card title="Ranking por puntaje" className="lg:col-span-3">
          <ResponsiveContainer width="100%" height={Math.max(350, chartData.length * 35)}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 40, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" horizontal={false} />
              <XAxis type="number" domain={[0, 10]} tick={{ fontSize: 11, fill: '#6B778C' }} axisLine={false} />
              <YAxis dataKey="company" type="category" width={160} tick={{ fontSize: 11, fill: '#172B4D' }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(v) => [v.toFixed(2), 'Puntaje']}
                contentStyle={{ borderRadius: 10, border: '1px solid #DFE1E6', fontSize: 13 }}
              />
              <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={22}>
                {chartData.map((entry) => (
                  <Cell key={entry.company} fill={entry.rank <= top7 ? '#36B37E' : '#44B3E1'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Table */}
        <Card title="Tabla de posiciones" className="lg:col-span-2">
          <div className="max-h-[500px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-border">
                  <th className="text-left py-2 px-2 text-xs text-muted font-semibold w-10">#</th>
                  <th className="text-left py-2 px-2 text-xs text-muted font-semibold">Empresa</th>
                  <th className="text-right py-2 px-2 text-xs text-muted font-semibold">Puntaje</th>
                  <th className="text-center py-2 px-2 text-xs text-muted font-semibold">Eval.</th>
                </tr>
              </thead>
              <tbody>
                {ranking.map((r) => (
                  <tr
                    key={r.company}
                    className={`border-b border-border/40 transition-colors
                      ${r.rank <= top7 ? 'bg-accent-light/50' : 'hover:bg-surface'}`}
                  >
                    <td className="py-2.5 px-2"><RankBadge rank={r.rank} /></td>
                    <td className={`py-2.5 px-2 ${r.rank <= top7 ? 'font-semibold text-primary-800' : 'text-primary-800/80'}`}>
                      {r.company}
                    </td>
                    <td className="py-2.5 px-2 text-right font-mono font-semibold tabular-nums">
                      {r.score.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-2 text-center">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-surface text-xs font-medium text-muted">
                        {r.evaluators}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Radar */}
      {radarData.length > 0 && (
        <Card title="Perfil comparativo - Top 5">
          <ResponsiveContainer width="100%" height={480}>
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
              <PolarGrid stroke="#DFE1E6" />
              <PolarAngleAxis dataKey="subcategory" tick={{ fontSize: 10, fill: '#6B778C' }} />
              <PolarRadiusAxis domain={[0, 10]} tick={{ fontSize: 10 }} />
              {radar.companies.map((comp, i) => (
                <Radar
                  key={comp}
                  name={comp}
                  dataKey={comp}
                  stroke={RADAR_COLORS[i % RADAR_COLORS.length]}
                  fill={RADAR_COLORS[i % RADAR_COLORS.length]}
                  fillOpacity={0.08}
                  strokeWidth={2}
                />
              ))}
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #DFE1E6', fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  );
}
