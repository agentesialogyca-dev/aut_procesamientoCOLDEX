import { useApi } from '../hooks/useApi';
import { getSubcategories, getHeatmap } from '../lib/api';
import Card from './Card';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

const COLORS_SCALE = ['#DE350B', '#FF8B00', '#FFAB00', '#36B37E', '#00875A'];

function getColor(val) {
  if (val == null) return '#DFE1E6';
  if (val < 2) return COLORS_SCALE[0];
  if (val < 4) return COLORS_SCALE[1];
  if (val < 6) return COLORS_SCALE[2];
  if (val < 8) return COLORS_SCALE[3];
  return COLORS_SCALE[4];
}

function SubcategoryBars({ data }) {
  const chartData = data
    .filter(d => d.average != null)
    .map(d => ({ name: d.name, value: d.average }))
    .sort((a, b) => a.value - b.value);

  return (
    <ResponsiveContainer width="100%" height={Math.max(350, chartData.length * 38)}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 40, top: 5, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" horizontal={false} />
        <XAxis type="number" domain={[0, 10]} tick={{ fontSize: 12, fill: '#6B778C' }} axisLine={false} />
        <YAxis dataKey="name" type="category" width={180} tick={{ fontSize: 11, fill: '#172B4D' }} axisLine={false} tickLine={false} />
        <Tooltip
          formatter={(v) => [v.toFixed(2), 'Promedio']}
          contentStyle={{ borderRadius: 10, border: '1px solid #DFE1E6', fontSize: 13 }}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={22}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={getColor(entry.value)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function HeatmapTable({ heatmap }) {
  const { subcategories, companies, values } = heatmap;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            <th className="text-left py-2 px-2 font-semibold text-muted sticky left-0 bg-card min-w-[160px]">Subcategoria</th>
            {companies.map(c => (
              <th key={c} className="py-2 px-1.5 font-medium text-muted text-center min-w-[70px]">
                <div className="truncate max-w-[80px]" title={c}>{c}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {subcategories.map((sub, ri) => (
            <tr key={sub}>
              <td className="py-1.5 px-2 font-medium text-primary-800 sticky left-0 bg-card">{sub}</td>
              {values[ri].map((val, ci) => (
                <td key={ci} className="py-1.5 px-1.5 text-center">
                  {val != null ? (
                    <div
                      className="rounded-md py-1 px-1 text-[11px] font-semibold mx-auto"
                      style={{
                        backgroundColor: getColor(val) + '22',
                        color: getColor(val),
                        minWidth: 44,
                      }}
                    >
                      {val.toFixed(1)}
                    </div>
                  ) : (
                    <span className="text-subtle">-</span>
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function OverviewTab({ sector, type }) {
  const { data: subcats, loading: l1 } = useApi(() => getSubcategories(sector, type), [sector, type]);
  const { data: heatmap, loading: l2 } = useApi(() => getHeatmap(sector, type), [sector, type]);

  if (l1 || l2) return <Skeleton />;

  return (
    <div className="space-y-5">
      <Card title="Promedio por subcategoria">
        <SubcategoryBars data={subcats} />
      </Card>
      <Card title="Mapa de calor por empresa">
        <HeatmapTable heatmap={heatmap} />
      </Card>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-5">
      {[1, 2].map(i => (
        <div key={i} className="bg-card rounded-xl border border-border h-64 animate-pulse" />
      ))}
    </div>
  );
}
