export default function LoadingScreen() {
  return (
    <div className="flex items-center justify-center h-screen bg-surface">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-muted text-sm font-medium tracking-wide uppercase">Cargando datos...</p>
      </div>
    </div>
  );
}
