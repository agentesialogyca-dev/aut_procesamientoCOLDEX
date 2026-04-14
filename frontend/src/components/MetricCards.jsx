import { FileText, Building2, Users, TrendingUp } from 'lucide-react';

const cards = [
  { key: 'records', label: 'Registros', icon: FileText, color: 'text-primary-600', bg: 'bg-primary-50', format: v => v?.toLocaleString() },
  { key: 'companies', label: 'Empresas evaluadas', icon: Building2, color: 'text-violet-600', bg: 'bg-violet-50' },
  { key: 'evaluators', label: 'Evaluadores', icon: Users, color: 'text-amber-600', bg: 'bg-amber-50' },
  { key: 'average', label: 'Promedio general', icon: TrendingUp, color: 'text-accent', bg: 'bg-accent-light', format: v => v?.toFixed(2) },
];

export default function MetricCards({ summary }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map(({ key, label, icon: Icon, color, bg, format }) => (
        <div key={key} className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 ${bg} rounded-lg flex items-center justify-center`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <p className="text-2xl font-bold text-primary-800 leading-none">
                {format ? format(summary[key]) : summary[key]}
              </p>
              <p className="text-xs text-muted mt-1 font-medium">{label}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
