from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from .constants import MissionStage


def _df_to_coord_block(df: pd.DataFrame) -> str:
    lines = [f"{row.lon:.7f},{row.lat:.7f},{row.gps_alt_m:.2f}" for row in df.itertuples(index=False)]
    return "\n          ".join(lines)


def export_mission_to_kml(
    df: pd.DataFrame,
    output_path: str | Path,
    mission_name: str = "NGM Planetary CanSat 2026-27",
) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    valid_df = df[df.get("is_valid", True) == True].copy()
    stage1_df = valid_df[valid_df["stage"] == int(MissionStage.STAGE_1_CANSAT_DESCENT)]
    stage2_df = valid_df[valid_df["stage"] == int(MissionStage.STAGE_2_DRONE_SCOUT)]
    placemarks: list[str] = []

    if len(stage1_df) > 1:
        placemarks.append(f"""
    <Placemark>
      <name>Stage 1: CanSat Parachute Descent</name>
      <styleUrl>#stage1Style</styleUrl>
      <LineString>
        <extrude>1</extrude><tessellate>1</tessellate><altitudeMode>absolute</altitudeMode>
        <coordinates>{_df_to_coord_block(stage1_df)}</coordinates>
      </LineString>
    </Placemark>""")

    if len(stage2_df) > 1:
        placemarks.append(f"""
    <Placemark>
      <name>Stage 2: Planetary Drone Scout Flight</name>
      <styleUrl>#stage2Style</styleUrl>
      <LineString>
        <extrude>1</extrude><tessellate>1</tessellate><altitudeMode>absolute</altitudeMode>
        <coordinates>{_df_to_coord_block(stage2_df)}</coordinates>
      </LineString>
    </Placemark>""")

    if len(stage1_df) > 0:
        apogee = stage1_df.loc[stage1_df["gps_alt_m"].idxmax()]
        placemarks.append(f"""
    <Placemark>
      <name>Apogee ({apogee.gps_alt_m:.1f}m MSL)</name>
      <Point><altitudeMode>absolute</altitudeMode><coordinates>{apogee.lon:.7f},{apogee.lat:.7f},{apogee.gps_alt_m:.2f}</coordinates></Point>
    </Placemark>""")

    if len(stage2_df) > 0:
        hotspot = stage2_df.loc[stage2_df["voc_r2_ohm"].idxmin()]
        placemarks.append(f"""
    <Placemark>
      <name>VOC Anomaly Hotspot ({hotspot.voc_r2_ohm/1000:.1f} kOhm)</name>
      <Point><altitudeMode>absolute</altitudeMode><coordinates>{hotspot.lon:.7f},{hotspot.lat:.7f},{hotspot.gps_alt_m:.2f}</coordinates></Point>
    </Placemark>""")

    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{escape(mission_name)}</name>
    <Style id="stage1Style"><LineStyle><color>ff0088ff</color><width>4</width></LineStyle><PolyStyle><color>400088ff</color></PolyStyle></Style>
    <Style id="stage2Style"><LineStyle><color>ff76e600</color><width>5</width></LineStyle><PolyStyle><color>4076e600</color></PolyStyle></Style>
    {"".join(placemarks)}
  </Document>
</kml>
"""
    out.write_text(kml_content, encoding="utf-8")
    return out
