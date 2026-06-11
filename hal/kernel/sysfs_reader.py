"""
hal/kernel/sysfs_reader.py
Reads hardware state from /sys filesystem.
All paths confirmed on AMD Ryzen 5 4500U.
"""
from __future__ import annotations
import logging, os
from pathlib import Path
from typing import Optional

log = logging.getLogger("hal.kernel.sysfs")

def read_file(path: str, default=None):
    try:
        return open(path).read().strip()
    except Exception:
        return default

def read_int(path: str, default: int = 0) -> int:
    val = read_file(path)
    try:
        return int(val) if val else default
    except ValueError:
        return default

def read_float(path: str, default: float = 0.0) -> float:
    val = read_file(path)
    try:
        return float(val) if val else default
    except ValueError:
        return default

# ── Battery (/sys/class/power_supply/BAT0) ──────────────────────────
BAT_BASE = "/sys/class/power_supply/BAT0"

def battery_level() -> float:
    cap = read_int(f"{BAT_BASE}/capacity", -1)
    return cap / 100.0 if cap >= 0 else -1.0

def battery_charging() -> bool:
    status = read_file(f"{BAT_BASE}/status", "Unknown")
    return status in ("Charging", "Full")

def battery_present() -> bool:
    return Path(BAT_BASE).exists()

# ── Thermal (/sys/class/thermal/thermal_zone*) ───────────────────────
def thermal_zones() -> list[dict]:
    zones = []
    base = Path("/sys/class/thermal")
    for tz in sorted(base.glob("thermal_zone*")):
        try:
            temp_mc = read_int(str(tz / "temp"), 0)
            zone_type = read_file(str(tz / "type"), "unknown")
            zones.append({
                "zone":    tz.name,
                "type":    zone_type,
                "temp_c":  round(temp_mc / 1000.0, 1),
            })
        except Exception:
            pass
    return zones

def cpu_temp_c() -> float:
    """Best CPU temp reading — k10temp preferred on AMD Ryzen."""
    # Try k10temp via hwmon
    for hwmon in Path("/sys/class/hwmon").glob("hwmon*"):
        name = read_file(str(hwmon / "name"), "")
        if "k10temp" in name:
            # Tctl is hwmon temp1
            t = read_int(str(hwmon / "temp1_input"), 0)
            if t > 0:
                return round(t / 1000.0, 1)
    # Fallback: acpitz thermal_zone0
    for tz in Path("/sys/class/thermal").glob("thermal_zone*"):
        tz_type = read_file(str(tz / "type"), "")
        if "acpitz" in tz_type or "x86_pkg_temp" in tz_type:
            t = read_int(str(tz / "temp"), 0)
            if 0 < t < 150000:
                return round(t / 1000.0, 1)
    return -1.0

# ── CPU frequency (/sys/devices/system/cpu) ─────────────────────────
def cpu_freq_mhz(core: int = 0) -> int:
    path = f"/sys/devices/system/cpu/cpu{core}/cpufreq/scaling_cur_freq"
    khz = read_int(path, 0)
    return khz // 1000 if khz else 0

def cpu_max_freq_mhz(core: int = 0) -> int:
    path = f"/sys/devices/system/cpu/cpu{core}/cpufreq/scaling_max_freq"
    khz = read_int(path, 0)
    return khz // 1000 if khz else 0

# ── NVMe (/sys/block/nvme0n1) ────────────────────────────────────────
def nvme_stats() -> dict:
    base = "/sys/block/nvme0n1"
    stat = read_file(f"{base}/stat", "")
    size_sectors = read_int(f"{base}/size", 0)
    return {
        "present":      Path(base).exists(),
        "size_gb":      round(size_sectors * 512 / 1e9, 1),
        "stat_raw":     stat,
    }
