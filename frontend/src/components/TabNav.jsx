import { BarChart3, Table2, Trophy, Users } from 'lucide-react';

const ICONS = { 'Resumen': BarChart3, 'Tabla Pivote': Table2, 'Ranking': Trophy, 'Evaluadores': Users };

export default function TabNav({ tabs, active, onChange }) {
  return (
    <div className="bg-card rounded-xl border border-border p-1.5 flex gap-1">
      {tabs.map(t => {
        const Icon = ICONS[t];
        const isActive = t === active;
        return (
          <button
            key={t}
            onClick={() => onChange(t)}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all
              ${isActive
                ? 'bg-primary-600 text-white shadow-sm'
                : 'text-muted hover:text-primary-800 hover:bg-surface'
              }`}
          >
            {Icon && <Icon className="w-4 h-4" />}
            {t}
          </button>
        );
      })}
    </div>
  );
}
