export type SeriesMensalRow = { mes: string; evasoes: number };
export type TopDestinoRow = { destino: string; total: number };
export type TopTrtRow = { trt: string; total: number };

async function loadJson<T>(path: string): Promise<T> {
  const base = import.meta.env.BASE_URL || "/";
  const url = new URL(path, window.location.origin + base).toString();

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Falha ao carregar ${url}: ${res.status}`);
  return res.json();
}


export async function loadAllData() {
  const [series, topDestinos, topTrts] = await Promise.all([
    loadJson<SeriesMensalRow[]>("data/series_mensal.json"),
    loadJson<TopDestinoRow[]>("data/top_destinos.json"),
    loadJson<TopTrtRow[]>("data/top_trts.json"),
  ]);

  return { series, topDestinos, topTrts };
}
