type Props = { label: string; value: string | number; hint?: string };

export function KpiCard({ label, value, hint }: Props) {
  return (
    <div className="kpi">
      <p className="kpiLabel">{label}</p>
      <p className="kpiValue">{value}</p>
      {hint ? <p className="kpiHint">{hint}</p> : null}
    </div>
  );
}
