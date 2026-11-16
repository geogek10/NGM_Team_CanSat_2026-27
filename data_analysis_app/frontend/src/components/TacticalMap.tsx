import type { AnalyzedRow, MissionSummary } from "../types/mission";

export function TacticalMap({ rows, summary }: { rows: AnalyzedRow[]; summary: MissionSummary }) {
  const valid = rows.filter((r) => r.is_valid && r.lat !== 0);
  if (valid.length < 2) return <div className="mono" style={{ padding: 20 }}>No valid GNSS coordinates.</div>;

  const lats = valid.map((r) => r.lat), lons = valid.map((r) => r.lon);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLon = Math.min(...lons), maxLon = Math.max(...lons);
  const spanLat = Math.max(0.0005, maxLat - minLat), spanLon = Math.max(0.0005, maxLon - minLon);

  const toXY = (lat: number, lon: number) => `${(40 + ((lon - minLon) / spanLon) * 520).toFixed(1)},${(260 - ((lat - minLat) / spanLat) * 220).toFixed(1)}`;
  const s1Pts = valid.filter((r) => r.stage === 1).map((r) => toXY(r.lat, r.lon)).join(" ");
  const s2Pts = valid.filter((r) => r.stage === 2).map((r) => toXY(r.lat, r.lon)).join(" ");
  const hs = summary.hotspotCoord;
  const hsXY = hs ? toXY(hs.lat, hs.lon).split(",").map(Number) : null;
  const launchXY = toXY(valid[0].lat, valid[0].lon).split(",").map(Number);

  return (
    <div style={{ background: "#050a18", borderRadius: 8, border: "1px solid #1e293b", overflow: "hidden" }}>
      <svg viewBox="0 0 600 300" style={{ width: "100%", height: 270, display: "block" }}>
        <defs><pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M 30 0 L 0 0 0 30" fill="none" stroke="#111d36" strokeWidth="1" /></pattern></defs>
        <rect width="600" height="300" fill="url(#grid)" />
        {s1Pts && <polyline fill="none" stroke="#fb923c" strokeWidth="3" strokeDasharray="5,4" points={s1Pts} />}
        {s2Pts && <polyline fill="none" stroke="#34d399" strokeWidth="3.5" points={s2Pts} />}
        <circle cx={launchXY[0]} cy={launchXY[1]} r="6" fill="#38bdf8" />
        <text x={launchXY[0] + 9} y={launchXY[1] + 4} fill="#38bdf8" fontSize="11" fontFamily="monospace">LAUNCHPAD</text>
        {hsXY && (<>
          <circle cx={hsXY[0]} cy={hsXY[1]} r="14" fill="rgba(244,63,94,0.22)" stroke="#f43f5e" strokeWidth="1.5" />
          <circle cx={hsXY[0]} cy={hsXY[1]} r="4" fill="#f43f5e" />
          <text x={hsXY[0] - 55} y={hsXY[1] - 18} fill="#fda4af" fontSize="11" fontFamily="monospace">CRATER / VOC ({hs?.sVoc.toFixed(0)}%)</text>
        </>)}
      </svg>
      <div style={{ display: "flex", gap: 14, padding: "8px 12px", fontSize: 11.5, borderTop: "1px solid #1e293b", color: "#94a3b8" }}>
        <span><strong style={{ color: "#38bdf8" }}>●</strong> Launchpad</span>
        <span><strong style={{ color: "#fb923c" }}>---</strong> Stage 1: Descent</span>
        <span><strong style={{ color: "#34d399" }}>—</strong> Stage 2: Drone</span>
        <span><strong style={{ color: "#f43f5e" }}>◎</strong> VOC Hotspot</span>
      </div>
    </div>
  );
}
