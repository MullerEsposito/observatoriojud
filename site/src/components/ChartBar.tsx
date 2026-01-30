import ReactECharts from "echarts-for-react";

type Row = { label: string; value: number };

export function ChartBar({ rows, height = 320 }: { rows: Row[]; height?: number }) {
  const labels = rows.map((r) => r.label);
  const values = rows.map((r) => r.value);

  const option = {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 24, right: 18, top: 10, bottom: 28, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { color: "rgba(231,237,247,0.75)" },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.08)" } },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
    },
    yAxis: {
      type: "category",
      data: labels,
      axisLabel: { color: "rgba(231,237,247,0.8)", width: 160, overflow: "truncate" },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
    },
    series: [
      {
        type: "bar",
        data: values,
        barMaxWidth: 18,
      },
    ],
  };

  return <ReactECharts option={option} style={{ height, width: "100%" }} />;
}
