import { useEffect, useMemo, useState } from "react";
import Papa from "papaparse";
import { Activity, Bot, CheckCircle2, Cloud, Compass, Download, FileSpreadsheet, Globe, Printer, ShieldCheck, Upload } from "lucide-react";
import { EChartBox } from "./components/EChartBox";
import { TacticalMap } from "./components/TacticalMap";
import type { RawTelemetryRow } from "./types/mission";
import { analyzeMission, buildKmlString } from "./utils/analyzer";

type Tab = "overview" | "atmosphere" | "ai" | "drone" | "validation";

const gaugeOpt = (title: string, value: number, color: string) => ({
  toolbox: { feature: { saveAsImage: { backgroundColor: "#0b1222" } } },
  series: [{
    type: "gauge", startAngle: 210, endAngle: -30, min: 0, max: 100,
    progress: { show: true, width: 12, itemStyle: { color } },
    axisLine: { lineStyle: { width: 12, color: [[1, "#1e293b"]] } },
    pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
    title: { offsetCenter: [0, "65%"], fontSize: 11, color: "#94a3b8" },
    detail: { valueAnimation: true, offsetCenter: [0, "5%"], fontSize: 22, fontWeight: "bold", color: "#f8fafc", formatter: "{value}%" },
    data: [{ value, name: title }],
  }],
});

export default function App() {
  const [tab, setTab] = useState<Tab>("overview");
  const [rawRows, setRawRows] = useState<RawTelemetryRow[]>([]);
  const [fileName, setFileName] = useState("Auto-loading...");

  const parseCsvText = (text: string, name: string, append = false) => {
    const res = Papa.parse<RawTelemetryRow>(text, { header: true, dynamicTyping: true, skipEmptyLines: true });
    const clean = res.data.filter((r) => r.timestamp_ms !== undefined && r.press_hpa !== undefined);
    setRawRows((prev) => (append ? [...prev, ...clean] : clean));
    setFileName((prev) => (append ? `${prev} + ${name}` : name));
  };

  useEffect(() => {
    fetch("/sample_flight.csv").then((r) => r.text()).then((t) => parseCsvText(t, "sample_flight.csv (Auto)")).catch(() => setFileName("Load CSV"));
  }, []);

  const handleFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    for (let i = 0; i < files.length; i++) parseCsvText(await files[i].text(), files[i].name, i > 0);
  };

  const { rows, summary } = useMemo(() => analyzeMission(rawRows, fileName), [rawRows, fileName]);
  const valid = useMemo(() => rows.filter((r) => r.is_valid), [rows]);
  const s1 = useMemo(() => valid.filter((r) => r.stage === 1), [valid]);
  const s2 = useMemo(() => valid.filter((r) => r.stage === 2), [valid]);

  const exportKml = () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([buildKmlString(rows)], { type: "application/vnd.google-earth.kml+xml" }));
    a.download = "ngm_cansat_3d_flight.kml";
    a.click();
  };

  const baseChart = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", backgroundColor: "#0f172a", borderColor: "#334155", textStyle: { color: "#e2e8f0" } },
    toolbox: { feature: { dataZoom: {}, saveAsImage: { backgroundColor: "#0b1222" } } },
    grid: { left: 48, right: 24, top: 36, bottom: 32 },
  };
  return (
    <div className="layout">
      <aside className="sidebar">
        <div style={{ padding: "6px 8px 14px", borderBottom: "1px solid #1e293b", marginBottom: 6 }}>
          <div className="mono" style={{ color: "#38bdf8", fontWeight: 700, fontSize: 15 }}>NGM CANSAT 2026-27</div>
          <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 3 }}>Planetary Aerial Scout Analytics</div>
        </div>
        {[
          ["overview", "Mission Overview", Compass], ["atmosphere", "Atmosphere (Stage 1)", Cloud],
          ["ai", "AI Gases & Habitability", Bot], ["drone", "Drone Scout & Power", Activity],
          ["validation", "Validation & Conclusions", ShieldCheck],
        ].map(([id, label, Icon]: any) => (
          <button key={id} className={`nav-btn ${tab === id ? "active" : ""}`} onClick={() => setTab(id)}>
            <Icon size={17} /> {label}
          </button>
        ))}
        <div style={{ marginTop: "auto", padding: 12, background: "#060b16", borderRadius: 8, border: "1px solid #1e293b", fontSize: 11, color: "#94a3b8" }}>
          <div style={{ color: "#e2e8f0", fontWeight: 600, marginBottom: 4 }}>Active Dataset</div>
          <div className="mono" style={{ wordBreak: "break-all" }}>{summary.fileName}</div>
          <div style={{ marginTop: 4 }}>{summary.totalRows} packets · QFE {summary.p0QfeHpa} hPa</div>
        </div>
      </aside>

      <main className="main">
        <div className="topbar no-print">
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700 }}>Mission Telemetry & AI Analytics Dashboard</h1>
            <span style={{ fontSize: 12, color: "#94a3b8" }}>Unified CSV Pipeline · Stage 1 CanSat Descent + Stage 2 Drone Scout</span>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <label className="btn btn-primary"><Upload size={15} /> Load CSV(s)<input type="file" accept=".csv" multiple hidden onChange={(e) => handleFiles(e.target.files)} /></label>
            <button className="btn" onClick={exportKml}><Globe size={15} /> Export 3D KML (Earth Studio)</button>
            <button className="btn" onClick={() => window.print()}><Printer size={15} /> Print / PDF Report</button>
          </div>
        </div>

        {tab === "overview" && (<>
          <div className="grid-4">
            <div className="card"><EChartBox height={175} option={gaugeOpt("Habitability Index", summary.avgHabitability, "#34d399")} /></div>
            <div className="card"><EChartBox height={175} option={gaugeOpt("Propulsion Health", summary.propulsionHealthPct, "#38bdf8")} /></div>
            <div className="card"><EChartBox height={175} option={gaugeOpt("Data Integrity", summary.integrityPct, "#fbbf24")} /></div>
            <div className="card"><EChartBox height={175} option={gaugeOpt("4S Batt Remaining", summary.batteryRemainingPct, "#a78bfa")} /></div>
          </div>
          <div className="grid-2">
            <div className="card"><div className="card-title"><span>2-Stage Geospatial Trajectory</span><span className="mono">APOGEE: {summary.apogeeM}m</span></div><TacticalMap rows={rows} summary={summary} /></div>
            <div className="card">
              <div className="card-title"><span>Stage 1 (CanSat) vs Stage 2 (Drone Scout)</span><FileSpreadsheet size={15} /></div>
              <table className="tbl">
                <thead><tr><th>Metric</th><th>Stage 1: CanSat</th><th>Stage 2: Drone</th></tr></thead>
                <tbody className="mono">
                  <tr><td>Samples</td><td>{s1.length}</td><td>{s2.length}</td></tr>
                  <tr><td>Max Altitude AGL</td><td>{summary.apogeeM} m</td><td>{s2.length ? Math.max(...s2.map((r) => r.baro_alt_m)).toFixed(1) : 0} m</td></tr>
                  <tr><td>Max Current Draw</td><td>{s1.length ? Math.max(...s1.map((r) => r.curr_a)).toFixed(2) : 0} A (Locked)</td><td>{s2.length ? Math.max(...s2.map((r) => r.curr_a)).toFixed(1) : 0} A</td></tr>
                  <tr><td>Mean Habitability</td><td>{s1.length ? (s1.reduce((a, b) => a + b.habitability_index, 0) / s1.length).toFixed(1) : 0}%</td><td>{s2.length ? (s2.reduce((a, b) => a + b.habitability_index, 0) / s2.length).toFixed(1) : 0}%</td></tr>
                  <tr><td>Min VOC Resistance</td><td>{s1.length ? (Math.min(...s1.map((r) => r.voc_r2_ohm)) / 1000).toFixed(1) : 0} kΩ</td><td style={{ color: "#f43f5e" }}>{s2.length ? (Math.min(...s2.map((r) => r.voc_r2_ohm)) / 1000).toFixed(1) : 0} kΩ</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </>)}
        {tab === "atmosphere" && (
          <div className="grid-2">
            <div className="card"><div className="card-title">Altitude AGL (m) vs Time (s)</div><EChartBox option={{ ...baseChart, xAxis: { type: "category", data: valid.map((r) => r.t_sec) }, yAxis: { type: "value", name: "m", splitLine: { lineStyle: { color: "#1e293b" } } }, series: [{ name: "Baro Alt", type: "line", smooth: true, showSymbol: false, lineStyle: { color: "#38bdf8", width: 2.5 }, areaStyle: { color: "rgba(56,189,248,0.12)" }, data: valid.map((r) => r.baro_alt_m) }] }} /></div>
            <div className="card"><div className="card-title"><span>Temperature (°C) vs Altitude (m)</span><span className="mono">Lapse: {summary.lapseRatePerKm} °C/km</span></div><EChartBox option={{ ...baseChart, xAxis: { type: "value", name: "°C", splitLine: { lineStyle: { color: "#1e293b" } } }, yAxis: { type: "value", name: "Alt (m)", splitLine: { lineStyle: { color: "#1e293b" } } }, series: [{ name: "Measured", type: "scatter", symbolSize: 5, itemStyle: { color: "#fb923c" }, data: s1.map((r) => [r.temp_c, r.baro_alt_m]) }] }} /></div>
            <div className="card"><div className="card-title">Pressure (hPa) vs Altitude (m)</div><EChartBox option={{ ...baseChart, xAxis: { type: "value", name: "hPa", min: "dataMin", splitLine: { lineStyle: { color: "#1e293b" } } }, yAxis: { type: "value", name: "Alt (m)", splitLine: { lineStyle: { color: "#1e293b" } } }, series: [{ name: "Pressure", type: "line", showSymbol: false, lineStyle: { color: "#a78bfa", width: 2.5 }, data: s1.map((r) => [r.press_hpa, r.baro_alt_m]) }] }} /></div>
            <div className="card"><div className="card-title">Air Density ρ (kg/m³) & Vertical Speed Vz (m/s)</div><EChartBox option={{ ...baseChart, legend: { textStyle: { color: "#94a3b8" } }, xAxis: { type: "category", data: s1.map((r) => r.t_sec) }, yAxis: [{ type: "value", name: "Vz", splitLine: { lineStyle: { color: "#1e293b" } } }, { type: "value", name: "ρ", splitLine: { show: false } }], series: [{ name: "Vz (m/s)", type: "line", showSymbol: false, lineStyle: { color: "#38bdf8" }, data: s1.map((r) => r.vz_mps) }, { name: "Density", type: "line", yAxisIndex: 1, showSymbol: false, lineStyle: { color: "#34d399" }, data: s1.map((r) => r.air_density) }] }} /></div>
          </div>
        )}

        {tab === "ai" && (
          <div className="grid-2">
            <div className="card"><div className="card-title">BME688 Heater Sweep (200°C vs 350°C) & AI S_VOC %</div><EChartBox option={{ ...baseChart, legend: { textStyle: { color: "#94a3b8" } }, xAxis: { type: "category", data: valid.map((r) => r.t_sec) }, yAxis: [{ type: "value", name: "kΩ", splitLine: { lineStyle: { color: "#1e293b" } } }, { type: "value", name: "S_VOC %", max: 100, splitLine: { show: false } }], series: [{ name: "R1 200°C", type: "line", showSymbol: false, lineStyle: { color: "#38bdf8" }, data: valid.map((r) => Math.round(r.voc_r1_ohm / 1000)) }, { name: "R2 350°C", type: "line", showSymbol: false, lineStyle: { color: "#34d399" }, data: valid.map((r) => Math.round(r.voc_r2_ohm / 1000)) }, { name: "S_VOC (%)", type: "line", yAxisIndex: 1, showSymbol: false, lineStyle: { color: "#f43f5e", width: 2 }, areaStyle: { color: "rgba(244,63,94,0.18)" }, data: valid.map((r) => r.s_voc_pct) }] }} /></div>
            <div className="card"><div className="card-title">HabitabilityNet: Zone Classification (Pie)</div><EChartBox option={{ tooltip: { trigger: "item" }, toolbox: { feature: { saveAsImage: { backgroundColor: "#0b1222" } } }, legend: { bottom: 0, textStyle: { color: "#94a3b8" } }, series: [{ type: "pie", radius: ["45%", "72%"], label: { color: "#e2e8f0" }, data: [{ value: summary.habBuckets.optimal, name: "Optimal (80-100%)", itemStyle: { color: "#34d399" } }, { value: summary.habBuckets.marginal, name: "Marginal (50-79%)", itemStyle: { color: "#fbbf24" } }, { value: summary.habBuckets.hostile, name: "Hostile (<50% / VOC)", itemStyle: { color: "#f43f5e" } }] }] }} /></div>
            <div className="card"><div className="card-title">GasSpecNet: Air Composition (Bar Chart)</div><EChartBox option={{ ...baseChart, xAxis: { type: "value", splitLine: { lineStyle: { color: "#1e293b" } } }, yAxis: { type: "category", data: Object.keys(summary.gasDist) }, series: [{ type: "bar", data: Object.values(summary.gasDist), itemStyle: { color: "#38bdf8", borderRadius: [0, 6, 6, 0] } }] }} /></div>
            <div className="card"><div className="card-title">Habitability Index (%) Over Timeline</div><EChartBox option={{ ...baseChart, xAxis: { type: "category", data: valid.map((r) => r.t_sec) }, yAxis: { type: "value", min: 0, max: 100, splitLine: { lineStyle: { color: "#1e293b" } } }, series: [{ name: "Habitability %", type: "line", showSymbol: false, lineStyle: { color: "#34d399", width: 2.5 }, areaStyle: { color: "rgba(52,211,153,0.16)" }, data: valid.map((r) => r.habitability_index) }] }} /></div>
          </div>
        )}

        {tab === "drone" && (
          <div className="grid-2">
            <div className="card"><div className="card-title">4S 120C Battery Voltage (V), Current (A) & Power (W)</div><EChartBox option={{ ...baseChart, legend: { textStyle: { color: "#94a3b8" } }, xAxis: { type: "category", data: s2.map((r) => r.t_sec) }, yAxis: [{ type: "value", name: "V / A", splitLine: { lineStyle: { color: "#1e293b" } } }, { type: "value", name: "W", splitLine: { show: false } }], series: [{ name: "Batt (V)", type: "line", showSymbol: false, lineStyle: { color: "#fbbf24" }, data: s2.map((r) => r.batt_v) }, { name: "Curr (A)", type: "line", showSymbol: false, lineStyle: { color: "#f43f5e" }, data: s2.map((r) => r.curr_a) }, { name: "Power (W)", type: "bar", yAxisIndex: 1, itemStyle: { color: "rgba(56,189,248,0.28)" }, data: s2.map((r) => r.power_w) }] }} /></div>
            <div className="card"><div className="card-title">AeroHealthNet: Drone vs Wheeled Rover (Comparison)</div><EChartBox option={{ ...baseChart, legend: { textStyle: { color: "#94a3b8" } }, xAxis: { type: "category", data: ["Crater Traversal (%)", "Distance (m)", "Survival (%)"] }, yAxis: { type: "value", splitLine: { lineStyle: { color: "#1e293b" } } }, series: [{ name: "Our Scout Drone", type: "bar", itemStyle: { color: "#34d399" }, data: [100, summary.droneDistanceM, 100] }, { name: "Wheeled Rover", type: "bar", itemStyle: { color: "#f43f5e" }, data: [0, 8.5, 15] }] }} /></div>
            <div className="card"><div className="card-title">Attitude Stability: Roll & Pitch (deg)</div><EChartBox option={{ ...baseChart, legend: { textStyle: { color: "#94a3b8" } }, xAxis: { type: "category", data: s2.map((r) => r.t_sec) }, yAxis: { type: "value", name: "deg", splitLine: { lineStyle: { color: "#1e293b" } } }, series: [{ name: "Roll", type: "line", showSymbol: false, lineStyle: { color: "#38bdf8" }, data: s2.map((r) => r.roll_deg) }, { name: "Pitch", type: "line", showSymbol: false, lineStyle: { color: "#a78bfa" }, data: s2.map((r) => r.pitch_deg) }] }} /></div>
            <div className="card"><div className="card-title">Stage 2 Scout KPIs</div><table className="tbl mono"><tbody><tr><td>Aerial Distance</td><td style={{ color: "#34d399" }}>{summary.droneDistanceM} m</td></tr><tr><td>Obstacles Bypassed</td><td>{summary.droneObstaclesBypassed}</td></tr><tr><td>Propulsion Health</td><td>{summary.propulsionHealthPct}%</td></tr><tr><td>VOC Hotspot</td><td style={{ color: "#f43f5e" }}>{summary.hotspotCoord ? `${summary.hotspotCoord.lat.toFixed(5)}°, ${summary.hotspotCoord.lon.toFixed(5)}°` : "None"}</td></tr></tbody></table></div>
          </div>
        )}

        {tab === "validation" && (
          <div className="grid-2">
            <div className="card"><div className="card-title">4-Stage Data Validation (Pie)</div><EChartBox option={{ tooltip: { trigger: "item" }, toolbox: { feature: { saveAsImage: { backgroundColor: "#0b1222" } } }, legend: { bottom: 0, textStyle: { color: "#94a3b8" } }, series: [{ type: "pie", radius: ["45%", "72%"], label: { color: "#e2e8f0" }, data: [{ value: summary.validRows, name: "Valid Samples", itemStyle: { color: "#34d399" } }, { value: summary.outlierRows, name: "MAD Spikes Rejected", itemStyle: { color: "#fbbf24" } }, { value: summary.boundsFailedRows, name: "Bounds Errors", itemStyle: { color: "#f43f5e" } }] }] }} /></div>
            <div className="card"><div className="card-title"><span>Baro Alt vs GPS Alt Consistency</span><span className="mono">MAE: {summary.baroVsGpsMaeM} m</span></div><EChartBox option={{ ...baseChart, legend: { textStyle: { color: "#94a3b8" } }, xAxis: { type: "category", data: valid.map((r) => r.t_sec) }, yAxis: { type: "value", name: "m", splitLine: { lineStyle: { color: "#1e293b" } } }, series: [{ name: "Baro AGL", type: "line", showSymbol: false, lineStyle: { color: "#38bdf8" }, data: valid.map((r) => r.baro_alt_m) }, { name: "GPS AGL", type: "line", showSymbol: false, lineStyle: { color: "#fb923c", type: "dashed" }, data: valid.map((r) => r.gps_alt_m - 50) }] }} /></div>
            <div className="card" style={{ gridColumn: "1 / -1" }}><div className="card-title"><span>Automated Scientific Conclusions</span><Download size={15} /></div><div style={{ display: "grid", gap: 10 }}>{summary.conclusions.map((c, idx) => (<div key={idx} style={{ display: "flex", gap: 10, padding: 12, background: "#060b16", borderRadius: 8, border: "1px solid #1e293b" }}><CheckCircle2 size={18} color="#34d399" style={{ flexShrink: 0, marginTop: 2 }} /><span style={{ fontSize: 13.5, lineHeight: 1.5 }}>{c}</span></div>))}</div></div>
          </div>
        )}
      </main>
    </div>
  );
}
