"""
hal/sensors/thermal.py
CPU/GPU thermal readings for AMD Ryzen 5 4500U.
Sources: k10temp hwmon, acpitz thermal_zone, NVMe sensors.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from hal.kernel.sysfs_reader import cpu_temp_c, thermal_zones

log = logging.getLogger("hal.sensors.thermal")

THROTTLE_WARN_C  = 85.0
THROTTLE_CRIT_C  = 95.0
THROTTLE_NVME_C  = 70.0

@dataclass
class ThermalState:
    cpu_temp_c:    float
    nvme_temp_c:   float
    all_zones:     list[dict]
    throttling:    bool
    warning:       bool

    @property
    def severity(self) -> str:
        if self.cpu_temp_c >= THROTTLE_CRIT_C:  return "CRITICAL"
        if self.cpu_temp_c >= THROTTLE_WARN_C:  return "HIGH"
        return "LOW"

def read() -> ThermalState:
    cpu  = cpu_temp_c()
    zones = thermal_zones()

    nvme_temp = -1.0
    for z in zones:
        if "nvme" in z["type"].lower() or "pcie" in z["type"].lower():
            nvme_temp = z["temp_c"]
            break

    throttling = cpu >= THROTTLE_CRIT_C
    warning    = cpu >= THROTTLE_WARN_C

    state = ThermalState(
        cpu_temp_c=cpu,
        nvme_temp_c=nvme_temp,
        all_zones=zones,
        throttling=throttling,
        warning=warning,
    )
    if throttling:
        log.error("CPU THERMAL THROTTLE: %.1f°C", cpu)
    elif warning:
        log.warning("CPU thermal warning: %.1f°C", cpu)
    return state
