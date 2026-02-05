import { useEffect, useMemo, useState } from "react";
import "./styles.css";
import { loadAllData, type SeriesMensalRow, type TopDestinoRow, type TopOrgaoRow } from "./lib/data";
import { sum } from "./lib/format";
import { Panel } from "./components/Panel";
import { KpiCard } from "./components/KpiCard";
import { ChartLine } from "./components/ChartLine";
import { ChartBar } from "./components/ChartBar";
import { Filters } from "./components/Filters";

type FiltersState = { start: string; end: string; orgao: string; destino: string };

export default function App() {
  const [loading, setLoading] = useState(true);
  const [series, setSeries] = useState<SeriesMensalRow[]>([]);
  const [topDestinos, setTopDestinos] = useState<TopDestinoRow[]>([]);
  const [topOrgaos, setTopOrgaos] = useState<TopOrgaoRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await loadAllData();
        setSeries(data.series);
        setTopDestinos(data.topDestinos);
        setTopOrgaos(data.topOrgaos);
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
    orgao: "",
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

  // Para o MVP (dados agregados separados), filtros de Orgao/destino ainda não “recalculam” tudo.
  // Eles vão funcionar de verdade quando o pipeline gerar agregados por dimensão.
  const orgaos = useMemo(() => topOrgaos.map((r) => r.orgao).sort(), [topOrgaos]);
  const destinos = useMemo(() => topDestinos.map((r) => r.destino).sort(), [topDestinos]);

  const barDestinos = useMemo(
    () => topDestinos.map((r) => ({ label: r.destino, value: r.total })),
    [topDestinos]
  );

  const barOrgaos = useMemo(() => {
    const sorted = [...topOrgaos].sort((a, b) => b.total - a.total); // decrescente
    return sorted.map((r, i) => ({
      label: `${i + 1}º ${r.orgao.toUpperCase()}`,
      value: r.total,
      details: r.details,
    }));
  }, [topOrgaos]);

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
          <h1 className="h1">Observatório — Evasão de TI (Órgãos Judiciários → fora)</h1>
          <p className="subtitle">
            Contagem pública agregada de saídas confirmadas de servidores(as) de tecnologia dos TRTs/TRFs/TREs
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
            trts={orgaos}
            destinos={destinos}
            value={{ ...filters, trt: filters.orgao }}
            onChange={(v) => setFilters({ ...v, orgao: v.trt })}
          />
          <hr className="hr" />
          <p className="subtitle">
            * No MVP, Órgão/Destino ainda não recalculam os gráficos porque os dados mock estão em
            agregados separados. Quando ligarmos o pipeline, vamos gerar agregados por dimensão
            e os filtros passam a funcionar de verdade.
          </p>
        </aside>

        <main style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="kpiRow">
            <KpiCard label="Evasões no período (total)" value={totalAno} hint="Confirmadas (destino fora do Judiciário identificado)" />
            <KpiCard label="Último mês" value={ultimoMes} hint="Consolidado do mês mais recente no dataset" />
            <KpiCard label="Cobertura" value="Órgãos (Admin)" hint="Cadernos administrativos analisados" />
          </div>

          <Panel title="Evolução mensal">
            <ChartLine rows={series} />
          </Panel>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Panel title="Top destinos (fora do Judiciário)">
              <ChartBar
                rows={[...barDestinos]
                  .sort((a, b) => b.value - a.value)
                  .map((r, i) => ({ ...r, label: `${i + 1}º ${r.label}` }))}
              />
            </Panel>

            <Panel title="Evasões (origem)">
              <ChartBar rows={barOrgaos} height={400} />
            </Panel>
          </div>
        </main>
      </div>
    </div>
  );
}
