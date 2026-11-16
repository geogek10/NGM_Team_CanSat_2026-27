export interface RawTelemetryRow {
  timestamp_ms: number; stage: number; state: number;
  lat: number; lon: number; gps_alt_m: number; sats: number; hdop: number;
  press_hpa: number; temp_c: number; hum_pct: number;
  voc_r1_ohm: number; voc_r2_ohm: number;
  roll_deg: number; pitch_deg: number; yaw_deg: number; acc_g: number;
  batt_v: number; curr_a: number; lq_pct: number;
}

export interface AnalyzedRow extends RawTelemetryRow {
  t_sec: number; baro_alt_m: number; vz_mps: number; air_density: number; power_w: number;
  is_valid: boolean; outlier_reason: string; s_voc_pct: number; habitability_index: number;
  gas_class: "Clean Air" | "VOC Plume" | "High Humidity" | "Thermal Artifact";
}

export interface MissionSummary {
  fileName: string; totalRows: number; validRows: number; outlierRows: number; boundsFailedRows: number;
  integrityPct: number; p0QfeHpa: number; apogeeM: number; maxDescentSpeedMps: number;
  lapseRatePerKm: number; baroVsGpsMaeM: number; avgHabitability: number; minHabitability: number;
  hotspotCoord: { lat: number; lon: number; alt: number; hi: number; sVoc: number } | null;
  habBuckets: { optimal: number; marginal: number; hostile: number };
  gasDist: Record<string, number>; propulsionHealthPct: number; batteryRemainingPct: number;
  droneDistanceM: number; droneObstaclesBypassed: number; conclusions: string[];
}
