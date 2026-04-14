import { useRef, useState } from 'react';
import { BarChart3, ChevronLeft, Download, Factory, Store, Loader2, Upload } from 'lucide-react';
import { exportExcel, processFile } from '../lib/api';

const SECTOR_ICONS = {
  TXT: '🧵', ELT: '⚡', CNS: '🛒', HGR: '🏠', SLD: '💊', SLDI: '🏥',
};

export default function Sidebar({ open, onToggle, filters, sector, type, onSectorChange, onTypeChange, file, onReloaded }) {
  const [exporting, setExporting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);

  const handleExport = async () => {
    if (!file) return;
    setExporting(true);
    try { await exportExcel(file); } finally { setExporting(false); }
  };

  const handleUpload = async (e) => {
    const newFile = e.target.files?.[0];
    if (!newFile) return;
    setUploadError(null);
    setUploading(true);
    try {
      await processFile(newFile);
      onReloaded?.(newFile);
    } catch (err) {
      setUploadError(err?.response?.data?.detail || 'Error al cargar');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <aside className={`${open ? 'w-64' : 'w-0'} flex-shrink-0 transition-all duration-300 overflow-hidden`}>
      <div className="w-64 h-full bg-gradient-to-b from-primary-800 to-primary-900 flex flex-col">
        {/* Logo */}
        <div className="px-5 pt-6 pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-white font-bold text-sm tracking-tight leading-none">Procesamiento LOGYCA</h1>
                <p className="text-primary-100/40 text-[10px] font-medium tracking-widest uppercase mt-0.5">COLDEX Sectorial</p>
              </div>
            </div>
            <button onClick={onToggle} className="text-white/30 hover:text-white/70 transition-colors">
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="h-px bg-white/[0.06] mx-4" />

        {/* Filters */}
        <div className="flex-1 px-4 py-5 space-y-5 overflow-y-auto">
          <div>
            <label className="text-[10px] font-semibold text-white/40 tracking-[0.1em] uppercase mb-2 block">
              Sector
            </label>
            <div className="space-y-1">
              {filters.sectors.map(s => (
                <button
                  key={s.code}
                  onClick={() => onSectorChange(s.code)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-sm transition-all
                    ${sector === s.code
                      ? 'bg-white/[0.12] text-white font-medium shadow-sm'
                      : 'text-white/50 hover:text-white/80 hover:bg-white/[0.05]'
                    }`}
                >
                  <span className="text-base">{SECTOR_ICONS[s.code]}</span>
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[10px] font-semibold text-white/40 tracking-[0.1em] uppercase mb-2 block">
              Tipo de empresa
            </label>
            <div className="space-y-1">
              {filters.types.map(t => {
                const Icon = t.code === 'INDUSTRIAL' ? Factory : Store;
                return (
                  <button
                    key={t.code}
                    onClick={() => onTypeChange(t.code)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-sm transition-all
                      ${type === t.code
                        ? 'bg-white/[0.12] text-white font-medium shadow-sm'
                        : 'text-white/50 hover:text-white/80 hover:bg-white/[0.05]'
                      }`}
                  >
                    <Icon className="w-4 h-4" />
                    {t.code}
                    <span className="text-[10px] text-white/30 ml-auto">{t.short}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="p-4 border-t border-white/[0.06] space-y-2">
          {file?.name && (
            <p className="text-[10px] text-white/40 truncate" title={file.name}>
              Archivo: <span className="text-white/70">{file.name}</span>
            </p>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={handleUpload}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold
                       bg-white/[0.08] text-white hover:bg-white/[0.14] disabled:opacity-60 transition-all"
          >
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            {uploading ? 'Cargando...' : 'Cargar Excel'}
          </button>
          {uploadError && (
            <p className="text-[10px] text-red-300">{uploadError}</p>
          )}
          <button
            onClick={handleExport}
            disabled={exporting}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold
                       bg-accent text-white hover:brightness-110 disabled:opacity-60 transition-all"
          >
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            {exporting ? 'Generando...' : 'Exportar Excel'}
          </button>
        </div>
      </div>
    </aside>
  );
}
