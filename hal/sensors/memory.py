"""
hal/sensors/memory.py
RAM + swap pressure monitoring via /proc/meminfo + psutil.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
import psutil

log = logging.getLogger("hal.sensors.memory")

RAM_WARN_PCT  = 0.85
RAM_CRIT_PCT  = 0.95
SWAP_WARN_PCT = 0.70

@dataclass
class MemoryState:
    total_gb:      float
    used_gb:       float
    available_gb:  float
    used_pct:      float
    swap_total_gb: float
    swap_used_gb:  float
    swap_pct:      float
    oom_risk:      bool

    @property
    def severity(self) -> str:
        if self.used_pct >= RAM_CRIT_PCT: return "CRITICAL"
        if self.used_pct >= RAM_WARN_PCT: return "HIGH"
        return "LOW"

def read() -> MemoryState:
    vm   = psutil.virtual_memory()
    swap = psutil.swap_memory()

    used_pct  = vm.used   / vm.total  if vm.total  else 0.0
    swap_pct  = swap.used / swap.total if swap.total else 0.0
    oom_risk  = used_pct >= RAM_CRIT_PCT and swap_pct >= SWAP_WARN_PCT

    state = MemoryState(
        total_gb     = round(vm.total  / 1e9, 2),
        used_gb      = round(vm.used   / 1e9, 2),
        available_gb = round(vm.available / 1e9, 2),
        used_pct     = round(used_pct, 3),
        swap_total_gb= round(swap.total / 1e9, 2),
        swap_used_gb = round(swap.used  / 1e9, 2),
        swap_pct     = round(swap_pct, 3),
        oom_risk     = oom_risk,
    )
    if oom_risk:
        log.error("OOM risk: RAM %.0f%% Swap %.0f%%",
                  used_pct*100, swap_pct*100)
    return state
