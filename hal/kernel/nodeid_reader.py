"""
hal/kernel/nodeid_reader.py
Reads NodeID from kernel driver or fallback file.
Same logic as chameha/identity.py — kept in sync.
"""
from __future__ import annotations
import hashlib, logging, os, uuid
from pathlib import Path
from typing import Optional

log = logging.getLogger("hal.kernel.nodeid")

NODE_ID_PATH     = os.getenv("NODE_ID_PATH", "/proc/sorabbyngo/nodeid")
NODE_ID_FALLBACK = Path(os.getenv("NODE_ID_FALLBACK",
                        os.path.expanduser("~/.sorabbyngo/nodeid")))
_cache: Optional[str] = None

def read_node_id() -> str:
    global _cache
    if _cache:
        return _cache
    # 1. kernel driver
    try:
        text = open(NODE_ID_PATH).read().strip()
        if text:
            _cache = text
            log.info("NodeID from kernel driver: %s...", text[:12])
            return _cache
    except (FileNotFoundError, PermissionError):
        pass
    # 2. fallback file
    try:
        if NODE_ID_FALLBACK.exists():
            text = NODE_ID_FALLBACK.read_text().strip()
            if text:
                _cache = text
                log.info("NodeID from fallback: %s...", text[:12])
                return _cache
    except Exception:
        pass
    # 3. derive from hardware
    machine_id = ""
    for p in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
        try:
            machine_id = open(p).read().strip(); break
        except Exception:
            pass
    nid = hashlib.sha256(f"{machine_id}:{hex(uuid.getnode())}".encode()).hexdigest()[:24]
    try:
        NODE_ID_FALLBACK.parent.mkdir(parents=True, exist_ok=True)
        NODE_ID_FALLBACK.write_text(nid)
    except Exception:
        pass
    log.info("NodeID derived (dev mode): %s...", nid[:12])
    _cache = nid
    return _cache
