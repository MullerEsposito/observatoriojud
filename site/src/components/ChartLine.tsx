import ReactECharts from "echarts-for-react";
import type { SeriesMensalRow } from "../lib/data";
import { formatMes } from "../lib/format";

export function ChartLine({ rows }: { rows: SeriesMensalRow[] }) {
  const x = rows.map((r) => formatMes(r.mes));
  const y = rows.map((r) => r.evasoes);

  const option = {
    tooltip: { trigger: "axis" },
    grid: { left: 24, right: 18, top: 20, bottom: 28, containLabel: true },
    xAxis: {
      type: "category",
      data: x,
      axisLabel: { color: "rgba(231,237,247,0.75)" },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "rgba(231,237,247,0.75)" },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.08)" } },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
    },
    series: [
      {
        type: "line",
        data: y,
        smooth: true,
        symbolSize: 8,
        lineStyle: { width: 3 },
        areaStyle: { opacity: 0.08 },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: 300, width: "100%" }} />;
}
