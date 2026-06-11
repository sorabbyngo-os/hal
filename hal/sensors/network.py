"""
hal/sensors/network.py
Network state: WiFi signal, internet, byngonet mesh.
"""
from __future__ import annotations
import logging, os, subprocess
from dataclasses import dataclass
import psutil

log = logging.getLogger("hal.sensors.network")

@dataclass
class NetworkState:
    interfaces:    dict        # name → bytes_sent/recv
    byngonet_up:   bool
    internet_up:   bool
    wifi_signal:   int         # dBm, 0 if unknown

def _wifi_signal() -> int:
    try:
        out = subprocess.check_output(
            ["iwconfig"], stderr=subprocess.DEVNULL, text=True, timeout=2
        )
        for line in out.splitlines():
            if "Signal level" in line:
                # Signal level=-52 dBm
                part = line.split("Signal level=")[-1].split()[0]
                return int(part.replace("dBm", "").strip())
    except Exception:
        pass
    return 0

def _internet_up() -> bool:
    try:
        subprocess.check_call(
            ["ping", "-c", "1", "-W", "1", "8.8.8.8"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=2
        )
        return True
    except Exception:
        return False

def _byngonet_up() -> bool:
    """Check if byngonet NATS is reachable."""
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    host = nats_url.replace("nats://", "").split(":")[0]
    port = int(nats_url.split(":")[-1]) if ":" in nats_url else 4222
    try:
        import socket
        s = socket.create_connection((host, port), timeout=1)
        s.close()
        return True
    except Exception:
        return False

def read() -> NetworkState:
    net_io = psutil.net_io_counters(pernic=True)
    interfaces = {
        iface: {"bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv}
        for iface, stats in net_io.items()
        if not iface.startswith("lo")
    }
    return NetworkState(
        interfaces  = interfaces,
        byngonet_up = _byngonet_up(),
        internet_up = _internet_up(),
        wifi_signal = _wifi_signal(),
    )
