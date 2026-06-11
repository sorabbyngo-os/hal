"""
hal/sensors/cpu.py
CPU load, frequency, per-core stats.
AMD Ryzen 5 4500U: 6 cores, no hyperthreading.
"""
from __future__ import annotations
import logging, os
from dataclasses import dataclass, field
from typing import List
import psutil
from hal.kernel.sysfs_reader import cpu_freq_mhz, cpu_max_freq_mhz

log = logging.getLogger("hal.sensors.cpu")

LOAD_WARN = 0.85
LOAD_CRIT = 0.95

@dataclass
class CPUState:
    core_count:    int
    load_avg_1:    float
    load_avg_5:    float
    load_avg_15:   float
    load_pct:      float       # overall 0.0-1.0
    per_core_pct:  List[float]
    freq_mhz:      int
    max_freq_mhz:  int

    @property
    def severity(self) -> str:
        if self.load_pct >= LOAD_CRIT: return "CRITICAL"
        if self.load_pct >= LOAD_WARN: return "HIGH"
        return "LOW"

def read() -> CPUState:
    cores     = psutil.cpu_count(logical=True) or 6
    load_avg  = os.getloadavg()
    load_pct  = load_avg[0] / cores
    per_core  = psutil.cpu_percent(interval=None, percpu=True)
    freq      = cpu_freq_mhz(0)
    max_freq  = cpu_max_freq_mhz(0)

    return CPUState(
        core_count   = cores,
        load_avg_1   = round(load_avg[0], 2),
        load_avg_5   = round(load_avg[1], 2),
        load_avg_15  = round(load_avg[2], 2),
        load_pct     = round(min(load_pct, 1.0), 3),
        per_core_pct = [round(p/100, 3) for p in (per_core or [])],
        freq_mhz     = freq,
        max_freq_mhz = max_freq,
    )
