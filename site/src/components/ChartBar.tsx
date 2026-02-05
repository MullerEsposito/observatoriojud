import { useState } from "react";
import ReactECharts from "echarts-for-react";

type Row = {
  label: string;
  value: number;
  details?: { nome: string; data: string; destino?: string; role?: string }[]
};

export function ChartBar({ rows, height = 320, showRanking = false }: { rows: Row[]; height?: number; showRanking?: boolean }) {
  const [expandedLabel, setExpandedLabel] = useState<string | null>(null);

  const labels = rows.map((r) => r.label);
  const data = rows.map((r) => ({
    value: r.value,
    details: r.details,
  }));

  const onChartClick = (params: any) => {
    const clickedLabel = params.name;
    setExpandedLabel(prev => prev === clickedLabel ? null : clickedLabel);
  };

  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params: any) => {
        const p = params[0];
        const name = p.name.includes('|') ? p.name.split('|')[1] : p.name;
        return `<strong>${name}</strong><br/>Total: ${p.value}<br/><span style="font-size:11px;color:#93a4bd">Clique para detalhes</span>`;
      }
    },
    grid: { left: 24, right: 18, top: 10, bottom: 28, containLabel: true },
    dataZoom: [
      {
        type: 'inside',
        yAxisIndex: 0,
        start: 0,
        end: Math.min(100, (10 / labels.length) * 100), // Show 10 items initially
        zoomOnMouseWheel: false,
        moveOnMouseWheel: true,
        moveOnMouseMove: false,
        preventDefaultMouseMove: false,
      }
    ],
    xAxis: {
      type: "value",
      axisLabel: { color: "rgba(231,237,247,0.75)" },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.08)" } },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: labels,
      axisLabel: {
        color: "rgba(231,237,247,0.8)",
        width: 160,
        overflow: "truncate",
        ...(showRanking && {
          formatter: (value: string) => {
            const [rank, name] = value.split('|');
            if (name) {
              return `{rank|${rank}}{name|${name}}`;
            }
            return value;
          },
          rich: {
            rank: {
              width: 35,
              align: 'left',
              color: "rgba(231,237,247,0.4)",
            },
            name: {
              width: 125,
              align: 'right',
            }
          }
        })
      },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
    },
    series: [
      {
        type: "bar",
        data: data,
        barMaxWidth: 18,
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: (params: any) => params.name === expandedLabel ? "#4369ff" : "#3b82f6"
        }
      },
    ],
  };

  const expandedRow = rows.find(r => r.label === expandedLabel);

  return (
    <div>
      <ReactECharts
        option={option}
        style={{ height, width: "100%" }}
        onEvents={{ 'click': onChartClick }}
      />

      {expandedRow && expandedRow.details && (
        <div className="servantList">
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4, fontWeight: 700 }}>
            SERVIDORES EM {expandedLabel?.includes('|') ? expandedLabel.split('|')[1] : expandedLabel}:
          </div>
          {expandedRow.details.map((d, i) => (
            <div key={i} className="servantItem">
              <span>{d.nome}</span>
              <span style={{ fontSize: 11, color: "var(--muted)" }}>
                {d.data.split("-").reverse().join("/")}
              </span>

              <div className="servantTooltip">
                <span className="tooltipTitle">Cargo Identificado</span>
                <span className="tooltipContent">{d.role || "Não identificado"}</span>
                <span className="tooltipTitle">Data do Ato</span>
                <span className="tooltipContent">{d.data.split("-").reverse().join("/")}</span>
                <span className="tooltipTitle">Destino</span>
                <span className="tooltipContent">{d.destino || "Outro Órgão"}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
