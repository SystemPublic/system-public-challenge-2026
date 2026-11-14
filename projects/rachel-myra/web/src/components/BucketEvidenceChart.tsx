"use client";

// Stacked bar: medicines per action bucket, split by evidence meter.
// Counts come straight from the knowledge base. Tree-shaken ECharts import.

import ReactEChartsCore from "echarts-for-react/lib/core";
import { BarChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";

echarts.use([BarChart, GridComponent, LegendComponent, TooltipComponent, SVGRenderer]);

export interface BucketEvidenceRow {
  bucket: string;
  strong: number;
  some: number;
  early: number;
}

export function BucketEvidenceChart({ rows }: { rows: BucketEvidenceRow[] }) {
  // Grey ramp for strength (dark = strong) so it doesn't compete with bucket colors.
  const series = [
    { key: "strong", name: "Strong", color: "#141414" },
    { key: "some", name: "Some", color: "#6b6b66" },
    { key: "early", name: "Early signs", color: "#c4c4bf" },
  ] as const;
  const option = {
    textStyle: { fontFamily: "inherit", color: "#141414" },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { top: 0 },
    grid: { left: 8, right: 16, top: 32, bottom: 8, containLabel: true },
    xAxis: { type: "value", minInterval: 1, name: "Medicines" },
    yAxis: { type: "category", data: rows.map((r) => r.bucket), inverse: true },
    series: series.map((s) => ({
      name: s.name,
      type: "bar",
      stack: "total",
      itemStyle: { color: s.color, borderColor: "#ffffff", borderWidth: 1 },
      data: rows.map((r) => r[s.key]),
    })),
  };
  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      opts={{ renderer: "svg" }}
      style={{ height: Math.max(160, rows.length * 44 + 60), width: "100%" }}
      aria-label="Medicines per action bucket by evidence strength"
    />
  );
}
