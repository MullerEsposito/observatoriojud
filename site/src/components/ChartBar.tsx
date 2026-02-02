import ReactECharts from "echarts-for-react";

type Row = {
  label: string;
  value: number;
  details?: { nome: string; data: string }[]
};

export function ChartBar({ rows, height = 320 }: { rows: Row[]; height?: number }) {
  const labels = rows.map((r) => r.label);
  const data = rows.map((r) => ({
    value: r.value,
    details: r.details,
  }));

  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params: any) => {
        const p = params[0];
        const row = rows[p.dataIndex];
        let res = `<strong>${p.name}</strong><br/>Total: ${p.value}`;
        if (row.details && row.details.length > 0) {
          res += "<br/><hr style='border:none;border-top:1px solid rgba(255,255,255,0.1);margin:4px 0'/>";
          row.details.forEach(d => {
            const date = d.data.split("-").reverse().join("/");
            res += `<div style="font-size:12px">${d.nome} - ${date}</div>`;
          });
        }
        return res;
      }
    },
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
        data: data,
        barMaxWidth: 18,
      },
    ],
  };

  return <ReactECharts option={option} style={{ height, width: "100%" }} />;
}
