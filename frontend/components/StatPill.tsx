interface StatPillProps {
  label: string;
  value: string | number;
}

export function StatPill({ label, value }: StatPillProps) {
  return (
    <div className="stat-pill">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}
