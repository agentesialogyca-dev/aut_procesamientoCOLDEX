import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import MetricCards from './components/MetricCards';
import TabNav from './components/TabNav';
import OverviewTab from './components/OverviewTab';
import PivotTab from './components/PivotTab';
import RankingTab from './components/RankingTab';
import EvaluatorsTab from './components/EvaluatorsTab';
import LoadingScreen from './components/LoadingScreen';
import UploadScreen from './components/UploadScreen';
import { getFilters, getSummary } from './lib/api';
import { useApi } from './hooks/useApi';

const TABS = ['Resumen', 'Tabla Pivote', 'Ranking', 'Evaluadores'];

export default function App() {
  const [sector, setSector] = useState('TXT');
  const [type, setType] = useState('INDUSTRIAL');
  const [tab, setTab] = useState('Resumen');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [file, setFile] = useState(null);
  const [reloadToken, setReloadToken] = useState(0);

  const { data: filters } = useApi(
    () => (file ? getFilters() : Promise.resolve(null)),
    [file, reloadToken],
  );
  const { data: summary, loading } = useApi(
    () => (file ? getSummary(sector, type) : Promise.resolve(null)),
    [sector, type, file, reloadToken],
  );

  useEffect(() => { setTab('Resumen'); }, [sector, type]);

  const handleLoaded = (loadedFile) => {
    setFile(loadedFile);
    setReloadToken((t) => t + 1);
  };

  if (!file) return <UploadScreen onLoaded={handleLoaded} />;
  if (!filters) return <LoadingScreen />;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        filters={filters}
        sector={sector}
        type={type}
        onSectorChange={setSector}
        onTypeChange={setType}
        file={file}
        onReloaded={handleLoaded}
      />

      <main className={`flex-1 overflow-y-auto transition-all duration-300 ${sidebarOpen ? 'ml-0' : 'ml-0'}`}>
        <div className="max-w-[1400px] mx-auto px-6 py-6">
          <Header
            sector={sector}
            type={type}
            filters={filters}
            sidebarOpen={sidebarOpen}
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          />

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : summary?.empty ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted">
              <div className="text-5xl mb-3 opacity-40">📭</div>
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">Selecciona otra combinacion de sector y tipo</p>
            </div>
          ) : (
            <>
              <MetricCards summary={summary} />
              <TabNav tabs={TABS} active={tab} onChange={setTab} />

              <div className="mt-5">
                {tab === 'Resumen' && <OverviewTab sector={sector} type={type} />}
                {tab === 'Tabla Pivote' && <PivotTab sector={sector} type={type} />}
                {tab === 'Ranking' && <RankingTab sector={sector} type={type} />}
                {tab === 'Evaluadores' && <EvaluatorsTab sector={sector} type={type} />}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
