export function formatMes(yyyyMm: string) {
  const [y, m] = yyyyMm.split("-").map((v) => Number(v));
  const dt = new Date(Date.UTC(y, m - 1, 1));
  return dt.toLocaleDateString("pt-BR", { month: "short", year: "numeric" }).replace(".", "");
}

export function sum(nums: number[]) {
  let t = 0;
  for (const n of nums) t += n;
  return t;
}
