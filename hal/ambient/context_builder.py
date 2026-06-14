"""
hal/ambient/context_builder.py
Builds ambient context snapshot every 30 seconds.
Published to chameha + byngox via NATS.
"""
from __future__ import annotations
import logging, os, time
from dataclasses import dataclass, field, asdict
from hal.sensors import thermal, battery, memory, cpu, storage, network
from hal.kernel.nodeid_reader import read_node_id

log = logging.getLogger("hal.ambient.context")

@dataclass
class AmbientContext:
    timestamp:   float
    node_id:     str
    battery:     dict = field(default_factory=dict)
    thermal:     dict = field(default_factory=dict)
    memory:      dict = field(default_factory=dict)
    cpu:         dict = field(default_factory=dict)
    storage:     dict = field(default_factory=dict)
    network:     dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        bat  = self.battery
        mem  = self.memory
        tmp  = self.thermal
        cpu_ = self.cpu
        return (
            f"Battery: {int(bat.get('level',0)*100)}% "
            f"({'charging' if bat.get('charging') else 'on battery'}) | "
            f"CPU: {cpu_.get('load_avg_1',0):.1f} load "
            f"{tmp.get('cpu_temp_c',0):.0f}°C | "
            f"RAM: {mem.get('used_gb',0):.1f}/{mem.get('total_gb',0):.1f}GB"
        )

def build() -> AmbientContext:
    node_id = read_node_id()
    # Suppress duplicate thermal logging — main.py poll loop already
    # logs thermal state; avoid double-logging on every ambient build
    import logging
    _thermal_logger = logging.getLogger("hal.sensors.thermal")
    _prev_level = _thermal_logger.level
    _thermal_logger.setLevel(logging.ERROR + 1)
    bat  = battery.read()
    thm  = thermal.read()
    mem  = memory.read()
    cpu_ = cpu.read()
    sto  = storage.read()
    net  = network.read()
    _thermal_logger.setLevel(_prev_level)

    def _s(obj):
        """Safe dataclass → dict, strip non-serializable."""
        try:
            return {k: v for k, v in obj.__dict__.items()
                    if isinstance(v, (str, int, float, bool, list, dict,
                                      type(None)))}
        except Exception:
            return {}

    ctx = AmbientContext(
        timestamp = time.time(),
        node_id   = node_id,
        battery   = _s(bat),
        thermal   = _s(thm),
        memory    = _s(mem),
        cpu       = _s(cpu_),
        storage   = _s(sto),
        network   = _s(net),
    )
    log.debug("Ambient: %s", ctx.summary())
    return ctx
