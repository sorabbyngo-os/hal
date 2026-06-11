"""
hal/sensors/storage.py
NVMe + USB storage health via psutil + sysfs.
Tracks: nvme0n1 (238GB root), sda1 (117GB models USB).
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import List
import psutil

log = logging.getLogger("hal.sensors.storage")

FREE_WARN_GB = 10.0
FREE_CRIT_GB = 3.0

@dataclass
class DiskState:
    device:    str
    mountpoint:str
    total_gb:  float
    used_gb:   float
    free_gb:   float
    used_pct:  float

@dataclass
class StorageState:
    disks:     List[DiskState] = field(default_factory=list)
    nvme_free_gb: float = 0.0
    usb_free_gb:  float = 0.0

    @property
    def severity(self) -> str:
        for d in self.disks:
            if d.free_gb <= FREE_CRIT_GB: return "CRITICAL"
            if d.free_gb <= FREE_WARN_GB: return "HIGH"
        return "LOW"

TRACKED_MOUNTS = {"/", "/media/sorabbyngo/models"}

def read() -> StorageState:
    disks = []
    for part in psutil.disk_partitions(all=False):
        if part.mountpoint not in TRACKED_MOUNTS:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            ds = DiskState(
                device     = part.device,
                mountpoint = part.mountpoint,
                total_gb   = round(usage.total / 1e9, 1),
                used_gb    = round(usage.used  / 1e9, 1),
                free_gb    = round(usage.free  / 1e9, 1),
                used_pct   = round(usage.percent / 100, 3),
            )
            disks.append(ds)
        except Exception as e:
            log.warning("disk_usage %s: %s", part.mountpoint, e)

    nvme_free = next((d.free_gb for d in disks if d.mountpoint == "/"), 0.0)
    usb_free  = next((d.free_gb for d in disks
                      if "models" in d.mountpoint), 0.0)

    state = StorageState(disks=disks, nvme_free_gb=nvme_free,
                         usb_free_gb=usb_free)
    if state.severity == "CRITICAL":
        log.error("Disk critically low: %s", [(d.mountpoint, d.free_gb)
                                               for d in disks])
    return state
