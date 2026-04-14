export default function Card({ title, icon, children, className = '' }) {
  return (
    <div className={`bg-card rounded-xl border border-border overflow-hidden ${className}`}>
      {title && (
        <div className="px-5 py-3.5 border-b border-border flex items-center gap-2">
          {icon && <span className="text-primary-600">{icon}</span>}
          <h3 className="text-sm font-semibold text-primary-800">{title}</h3>
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}
