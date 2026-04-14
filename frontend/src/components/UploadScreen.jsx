import { useRef, useState } from 'react';
import { BarChart3, Upload, Loader2, FileSpreadsheet } from 'lucide-react';
import { processFile } from '../lib/api';

export default function UploadScreen({ onLoaded }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = async (file) => {
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      await processFile(file);
      onLoaded(file);
    } catch (e) {
      setError(e?.response?.data?.detail || 'No se pudo cargar el archivo');
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  };

  return (
    <div className="flex items-center justify-center h-screen bg-surface px-6">
      <div className="w-full max-w-xl">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-11 h-11 bg-primary-600 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-primary-800 font-bold text-xl tracking-tight leading-none">COLDEX Sectorial</h1>
            <p className="text-muted text-[11px] font-medium tracking-widest uppercase mt-1">Dashboard 2025</p>
          </div>
        </div>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => !uploading && inputRef.current?.click()}
          className={`cursor-pointer border-2 border-dashed rounded-xl p-10 text-center transition-all
            ${dragging ? 'border-primary-600 bg-primary-50' : 'border-border bg-white hover:border-primary-400 hover:bg-primary-50/40'}
            ${uploading ? 'pointer-events-none opacity-60' : ''}`}
        >
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-full bg-primary-50 flex items-center justify-center">
              {uploading ? (
                <Loader2 className="w-6 h-6 text-primary-600 animate-spin" />
              ) : (
                <FileSpreadsheet className="w-6 h-6 text-primary-600" />
              )}
            </div>
            <div>
              <p className="text-base font-semibold text-primary-800">
                {uploading ? 'Cargando archivo...' : 'Carga tu archivo Excel'}
              </p>
              <p className="text-sm text-muted mt-1">
                Arrastra el .xlsx aqui o haz clic para seleccionarlo
              </p>
            </div>

            {!uploading && (
              <button
                type="button"
                className="mt-2 inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-accent text-white hover:brightness-110 transition-all"
              >
                <Upload className="w-4 h-4" />
                Seleccionar archivo
              </button>
            )}
          </div>

          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
        </div>

        {error && (
          <p className="mt-4 text-sm text-red-600 text-center font-medium">{error}</p>
        )}
      </div>
    </div>
  );
}
