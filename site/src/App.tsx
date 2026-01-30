import { useEffect, useMemo, useState } from "react";
import "./styles.css";
import { loadAllData, type SeriesMensalRow, type TopDestinoRow, type TopTrtRow } from "./lib/data";
import { sum } from "./lib/format";
import { Panel } from "./components/Panel";
import { KpiCard } from "./components/KpiCard";
import { ChartLine } from "./components/ChartLine";
import { ChartBar } from "./components/ChartBar";
import { Filters } from "./components/Filters";

type FiltersState = { start: string; end: string; trt: string; destino: string };

export default function App() {
  const [loading, setLoading] = useState(true);
  const [series, setSeries] = useState<SeriesMensalRow[]>([]);
  const [topDestinos, setTopDestinos] = useState<TopDestinoRow[]>([]);
  const [topTrts, setTopTrts] = useState<TopTrtRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await loadAllData();
        setSeries(data.series);
        setTopDestinos(data.topDestinos);
        setTopTrts(data.topTrts);
      } catch (e: any) {
        setError(e?.message ?? "Falha ao carregar dados.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const minMes = useMemo(() => (series[0]?.mes ?? "2025-01"), [series]);
  const maxMes = useMemo(() => (series.at(-1)?.mes ?? "2026-01"), [series]);

  const [filters, setFilters] = useState<FiltersState>({
    start: minMes,
    end: maxMes,
    trt: "",
    destino: "",
  });

  // Atualiza start/end quando dados chegam
  useEffect(() => {
    if (!series.length) return;
    setFilters((f) => ({
      ...f,
      start: series[0].mes,
      end: series.at(-1)!.mes,
    }));
  }, [series]);

  const totalAno = useMemo(() => sum(series.map((r) => r.evasoes)), [series]);
  const ultimoMes = useMemo(() => (series.at(-1)?.evasoes ?? 0), [series]);

  // Para o MVP (dados agregados separados), filtros de TRT/destino ainda não “recalculam” tudo.
  // Eles vão funcionar de verdade quando o pipeline gerar agregados por dimensão.
  const trts = useMemo(() => topTrts.map((r) => r.trt).sort(), [topTrts]);
  const destinos = useMemo(() => topDestinos.map((r) => r.destino).sort(), [topDestinos]);

  const barDestinos = useMemo(
    () => topDestinos.slice(0, 10).map((r) => ({ label: r.destino, value: r.total })),
    [topDestinos]
  );

  const barTrts = useMemo(
    () => topTrts.slice(0, 10).map((r) => ({ label: r.trt, value: r.total })),
    [topTrts]
  );

  if (loading) {
    return (
      <div className="container">
        <div className="panel">Carregando…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="panel">
          <strong>Erro:</strong> {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <header className="header">
        <div className="title">
          <h1 className="h1">Observatório — Evasão de TI (TRTs → fora do Judiciário)</h1>
          <p className="subtitle">
            Contagem pública agregada de saídas confirmadas de servidores(as) de tecnologia dos TRTs
            para órgãos fora do Poder Judiciário.
          </p>
        </div>
        <span className="badge">Fonte: Diários Oficiais (pipeline automático)</span>
      </header>

      <div className="grid">
        <aside className="panel">
          <h3 className="panelTitle">Filtros</h3>
          <Filters
            minMes={minMes}
            maxMes={maxMes}
            trts={trts}
            destinos={destinos}
            value={filters}
            onChange={setFilters}
          />
          <hr className="hr" />
          <p className="subtitle">
            * No MVP, TRT/Destino ainda não recalculam os gráficos porque os dados mock estão em
            agregados separados. Quando ligarmos o pipeline, vamos gerar agregados por TRT/destino
            por mês e os filtros passam a funcionar de verdade.
          </p>
        </aside>

        <main style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="kpiRow">
            <KpiCard label="Evasões no período (total)" value={totalAno} hint="Confirmadas (destino fora do Judiciário identificado)" />
            <KpiCard label="Último mês" value={ultimoMes} hint="Consolidado do mês mais recente no dataset" />
            <KpiCard label="Cobertura" value="TRTs (Admin)" hint="Cadernos administrativos por tribunal" />
          </div>

          <Panel title="Evolução mensal">
            <ChartLine rows={series} />
          </Panel>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Panel title="Top destinos (fora do Judiciário)">
              <ChartBar rows={barDestinos} />
            </Panel>

            <Panel title="Top TRTs (origem)">
              <ChartBar rows={barTrts} />
            </Panel>
          </div>
        </main>
      </div>
    </div>
  );
}
