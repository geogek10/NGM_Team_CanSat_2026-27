import { useEffect, useRef } from "react";
import * as echarts from "echarts";

export function EChartBox({ option, height = 265 }: { option: echarts.EChartsCoreOption; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current, undefined, { renderer: "canvas" });
    chartRef.current = chart;
    const obs = new ResizeObserver(() => chart.resize());
    obs.observe(ref.current);
    return () => { obs.disconnect(); chart.dispose(); };
  }, []);

  useEffect(() => { chartRef.current?.setOption(option, true); }, [option]);

  return <div ref={ref} style={{ width: "100%", height }} />;
}
