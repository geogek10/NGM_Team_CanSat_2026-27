import csv
from pathlib import Path
from typing import Dict, TextIO
from core.cansat_physics import CSV_COLUMNS


class AtomicMissionLogger:
    """Γράφει ακαριαία κάθε πακέτο σε CSV (Στάδιο 1 & Στάδιο 2) με flush()."""

    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = Path(logs_dir)                # Φάκελος αποθήκευσης logs/
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._files: Dict[int, TextIO] = {}           # Ανοιχτά αρχεία ανά στάδιο
        self._writers: Dict[int, csv.DictWriter] = {} # Εγγραφείς CSV ανά στάδιο

    def _get_writer(self, stage: int) -> csv.DictWriter:
        if stage not in self._writers:
            # Διαφορετικό όνομα ανά στάδιο, ΑΚΡΙΒΩΣ η ίδια δομή στηλών CSV_COLUMNS!
            fname = "stage1_descent.csv" if stage == 1 else "stage2_drone_scout.csv"
            fpath = self.logs_dir / fname
            is_new = not fpath.exists() or fpath.stat().st_size == 0
            f = open(fpath, mode="a", newline="", encoding="utf-8")
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            if is_new:
                writer.writeheader()                  # Γράφουμε τις 20 κεφαλίδες αν είναι νέο
                f.flush()
            self._files[stage] = f
            self._writers[stage] = writer
        return self._writers[stage]

    def log_packet(self, pkt: Dict[str, float]) -> None:
        stage = int(pkt.get("stage", 1))              # 1 = CanSat, 2 = Drone
        self._get_writer(stage).writerow(pkt)         # Εγγραφή γραμμής
        self._files[stage].flush()                    # Άμεσο σώσιμο στον δίσκο!

    def close(self) -> None:
        for f in self._files.values():                # Ασφαλές κλείσιμο όλων των αρχείων
            f.flush()
            f.close()
        self._files.clear()
        self._writers.clear()
