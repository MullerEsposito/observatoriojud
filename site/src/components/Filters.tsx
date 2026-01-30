type Props = {
  minMes: string;
  maxMes: string;
  trts: string[];
  destinos: string[];
  value: { start: string; end: string; trt: string; destino: string };
  onChange: (next: Props["value"]) => void;
};

export function Filters({ minMes, maxMes, trts, destinos, value, onChange }: Props) {
  return (
    <div className="filters">
      <div className="field">
        <label>Período (início)</label>
        <input
          type="month"
          min={minMes}
          max={maxMes}
          value={value.start}
          onChange={(e) => onChange({ ...value, start: e.target.value })}
        />
      </div>

      <div className="field">
        <label>Período (fim)</label>
        <input
          type="month"
          min={minMes}
          max={maxMes}
          value={value.end}
          onChange={(e) => onChange({ ...value, end: e.target.value })}
        />
      </div>

      <div className="field">
        <label>TRT (origem)</label>
        <select value={value.trt} onChange={(e) => onChange({ ...value, trt: e.target.value })}>
          <option value="">Todos</option>
          {trts.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label>Destino (fora do Judiciário)</label>
        <select
          value={value.destino}
          onChange={(e) => onChange({ ...value, destino: e.target.value })}
        >
          <option value="">Todos</option>
          {destinos.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>

      <span className="badge">⚠️ Dados mock (MVP do dashboard)</span>
    </div>
  );
}
