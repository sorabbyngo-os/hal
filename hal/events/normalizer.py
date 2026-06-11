"""
hal/events/normalizer.py
Converts sensor readings into ChamehaEvents.
Matches the ChamehaEvent format in chameha/event_bus.py.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class EventType(str, Enum):
    LOCK   = "LOCK"
    ASK    = "ASK"
    NOTIFY = "NOTIFY"

class Severity(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class HALEvent:
    source:       str
    event_type:   EventType
    severity:     Severity
    message:      str
    data:         dict       = field(default_factory=dict)
    action_taken: Optional[str] = None
    confidence:   float      = 1.0
    timestamp:    float      = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "source":       self.source,
            "event_type":   self.event_type.value,
            "severity":     self.severity.value,
            "message":      self.message,
            "data":         self.data,
            "action_taken": self.action_taken,
            "confidence":   self.confidence,
            "timestamp":    self.timestamp,
        }

def from_thermal(state) -> Optional[HALEvent]:
    if state.cpu_temp_c <= 0:
        return None
    if state.throttling:
        return HALEvent(
            source="hal.thermal", event_type=EventType.LOCK,
            severity=Severity.CRITICAL,
            message=f"CPU thermal throttle active. Temperature: {state.cpu_temp_c}°C.",
            data={"cpu_temp_c": state.cpu_temp_c},
        )
    if state.warning:
        return HALEvent(
            source="hal.thermal", event_type=EventType.NOTIFY,
            severity=Severity.HIGH,
            message=f"CPU approaching thermal throttle. Temperature: {state.cpu_temp_c}°C.",
            data={"cpu_temp_c": state.cpu_temp_c},
        )
    return None

def from_battery(state) -> Optional[HALEvent]:
    if not state.present or state.charging:
        return None
    if state.severity == "CRITICAL":
        return HALEvent(
            source="hal.battery", event_type=EventType.LOCK,
            severity=Severity.CRITICAL,
            message=f"Battery critically low: {int(state.level*100)}%. Connect power.",
            data={"level": state.level},
        )
    if state.severity == "HIGH":
        return HALEvent(
            source="hal.battery", event_type=EventType.NOTIFY,
            severity=Severity.HIGH,
            message=f"Battery low: {int(state.level*100)}%.",
            data={"level": state.level},
        )
    return None

def from_memory(state) -> Optional[HALEvent]:
    if state.oom_risk:
        return HALEvent(
            source="hal.memory", event_type=EventType.LOCK,
            severity=Severity.CRITICAL,
            message=f"OOM risk. RAM: {state.used_pct*100:.0f}% used. Swap: {state.swap_pct*100:.0f}% used.",
            data={"used_pct": state.used_pct, "swap_pct": state.swap_pct},
        )
    if state.severity == "HIGH":
        return HALEvent(
            source="hal.memory", event_type=EventType.NOTIFY,
            severity=Severity.HIGH,
            message=f"RAM pressure: {state.used_gb:.1f}GB / {state.total_gb:.1f}GB used.",
            data={"used_gb": state.used_gb, "available_gb": state.available_gb},
        )
    return None

def from_storage(state) -> Optional[HALEvent]:
    if state.severity == "CRITICAL":
        low = [(d.mountpoint, d.free_gb) for d in state.disks
               if d.free_gb <= 3.0]
        return HALEvent(
            source="hal.storage", event_type=EventType.LOCK,
            severity=Severity.CRITICAL,
            message=f"Disk critically low: {low}",
            data={"disks": [d.__dict__ for d in state.disks]},
        )
    if state.severity == "HIGH":
        return HALEvent(
            source="hal.storage", event_type=EventType.NOTIFY,
            severity=Severity.HIGH,
            message=f"Disk space low. NVMe free: {state.nvme_free_gb}GB.",
            data={"nvme_free_gb": state.nvme_free_gb},
        )
    return None

def from_network(state) -> Optional[HALEvent]:
    if not state.byngonet_up:
        return HALEvent(
            source="hal.network", event_type=EventType.NOTIFY,
            severity=Severity.HIGH,
            message="Byngonet mesh unavailable. Falling back to offline mode.",
            data={"byngonet_up": False},
        )
    return None
