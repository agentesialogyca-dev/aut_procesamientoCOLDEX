import { Menu, Factory, Store } from 'lucide-react';

const SECTOR_NAMES = {
  TXT: 'Textil', ELT: 'Electro', CNS: 'Consumo', HGR: 'Hogar', SLD: 'Salud', SLDI: 'Salud Insumos',
};

export default function Header({ sector, type, sidebarOpen, onToggleSidebar }) {
  const Icon = type === 'INDUSTRIAL' ? Factory : Store;

  return (
    <div className="flex items-center gap-3 mb-6">
      {!sidebarOpen && (
        <button
          onClick={onToggleSidebar}
          className="w-9 h-9 flex items-center justify-center rounded-lg border border-border hover:bg-white transition-colors"
        >
          <Menu className="w-4 h-4 text-muted" />
        </button>
      )}
      <div>
        <h1 className="text-2xl font-bold text-primary-800 tracking-tight">
          {SECTOR_NAMES[sector] || sector}
        </h1>
      </div>
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-50 text-primary-600 text-xs font-semibold">
        <Icon className="w-3.5 h-3.5" />
        {type}
      </span>
    </div>
  );
}
