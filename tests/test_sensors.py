"""
tests/test_sensors.py
Smoke tests — verify sensors read without crashing.
No mocking — reads real hardware.
"""
import pytest

def test_thermal():
    from hal.sensors.thermal import read
    s = read()
    assert s.cpu_temp_c >= 0 or s.cpu_temp_c == -1.0
    assert s.severity in ("LOW", "HIGH", "CRITICAL")
    print(f"CPU temp: {s.cpu_temp_c}°C severity={s.severity}")

def test_battery():
    from hal.sensors.battery import read
    s = read()
    assert s.severity in ("LOW", "HIGH", "CRITICAL")
    print(f"Battery: {s.level*100:.0f}% charging={s.charging}")

def test_memory():
    from hal.sensors.memory import read
    s = read()
    assert s.total_gb > 0
    assert 0.0 <= s.used_pct <= 1.0
    print(f"RAM: {s.used_gb:.1f}/{s.total_gb:.1f}GB swap={s.swap_used_gb:.1f}GB")

def test_cpu():
    from hal.sensors.cpu import read
    s = read()
    assert s.core_count > 0
    assert s.load_avg_1 >= 0
    print(f"CPU: {s.core_count} cores load={s.load_avg_1} freq={s.freq_mhz}MHz")

def test_storage():
    from hal.sensors.storage import read
    s = read()
    assert s.nvme_free_gb >= 0
    print(f"NVMe: {s.nvme_free_gb}GB free, USB: {s.usb_free_gb}GB free")

def test_nodeid():
    from hal.kernel.nodeid_reader import read_node_id
    nid = read_node_id()
    assert len(nid) >= 16
    print(f"NodeID: {nid[:16]}...")

def test_context_build():
    from hal.ambient.context_builder import build
    ctx = build()
    assert ctx.node_id
    assert ctx.timestamp > 0
    print(f"Context: {ctx.summary()}")

def test_event_normalizer():
    from hal.sensors.thermal import read
    from hal.events.normalizer import from_thermal
    state = read()
    event = from_thermal(state)
    if event:
        assert event.source == "hal.thermal"
        print(f"Thermal event: {event.severity.value} — {event.message}")
    else:
        print("No thermal event (normal temps)")
