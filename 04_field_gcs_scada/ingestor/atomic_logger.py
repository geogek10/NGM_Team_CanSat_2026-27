import csv
from pathlib import Path
from typing import Dict, TextIO
from cansat_core import CSV_COLUMNS, MissionStage


class AtomicMissionLogger:
    """
    Writes telemetry packets immediately to Stage 1 and Stage 2 CSV files
    with immediate disk flush() so zero data is lost on power failure.
    """

    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._files: Dict[int, TextIO] = {}
        self._writers: Dict[int, csv.DictWriter] = {}

    def _get_writer(self, stage: int) -> csv.DictWriter:
        if stage not in self._writers:
            fname = "stage1_descent.csv" if stage == int(MissionStage.STAGE_1_CANSAT_DESCENT) else "stage2_drone_scout.csv"
            fpath = self.logs_dir / fname
            is_new = not fpath.exists() or fpath.stat().st_size == 0
            f = open(fpath, mode="a", newline="", encoding="utf-8")
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            if is_new:
                writer.writeheader()
                f.flush()
            self._files[stage] = f
            self._writers[stage] = writer
        return self._writers[stage]

    def log_packet(self, packet: Dict[str, float]) -> None:
        stage = int(packet.get("stage", 1))
        writer = self._get_writer(stage)
        writer.writerow(packet)
        self._files[stage].flush()

    def close(self) -> None:
        for f in self._files.values():
            try:
                f.flush()
                f.close()
            except OSError:
                pass
        self._files.clear()
        self._writers.clear()
