"""
hal/sensors/battery.py
Battery state for laptop — /sys/class/power_supply/BAT0
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from hal.kernel.sysfs_reader import (
    battery_level, battery_charging, battery_present, read_file, BAT_BASE
)

log = logging.getLogger("hal.sensors.battery")

LOW_WARN   = 0.20
LOW_CRIT   = 0.10

@dataclass
class BatteryState:
    present:   bool
    level:     float        # 0.0 - 1.0
    charging:  bool
    status:    str
    health:    str

    @property
    def severity(self) -> str:
        if not self.present:         return "LOW"
        if self.level <= LOW_CRIT:   return "CRITICAL"
        if self.level <= LOW_WARN:   return "HIGH"
        return "LOW"

def read() -> BatteryState:
    if not battery_present():
        return BatteryState(
            present=False, level=-1.0,
            charging=False, status="absent", health="unknown"
        )
    level    = battery_level()
    charging = battery_charging()
    status   = read_file(f"{BAT_BASE}/status", "Unknown")
    health   = read_file(f"{BAT_BASE}/health", "Good")

    state = BatteryState(
        present=True, level=level,
        charging=charging, status=status, health=health
    )
    if state.severity == "CRITICAL" and not charging:
        log.error("Battery critical: %.0f%%", level * 100)
    elif state.severity == "HIGH" and not charging:
        log.warning("Battery low: %.0f%%", level * 100)
    return state
