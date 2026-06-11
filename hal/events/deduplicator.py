"""
hal/events/deduplicator.py
Suppresses repeated events from same source within window.
Matches chameha brain.py DEDUP_WINDOW logic.
"""
from __future__ import annotations
import threading, time
from hal.events.normalizer import HALEvent

DEDUP_WINDOWS = {
    "CRITICAL": 10,
    "HIGH":     30,
    "MEDIUM":   60,
    "LOW":      120,
}

class Deduplicator:
    def __init__(self):
        self._lock    = threading.Lock()
        self._seen:   dict[str, float] = {}

    def is_duplicate(self, event: HALEvent) -> bool:
        key    = f"{event.source}:{event.message[:40]}"
        window = DEDUP_WINDOWS.get(event.severity.value, 30)
        with self._lock:
            last = self._seen.get(key)
            if last and (time.time() - last) < window:
                return True
            self._seen[key] = time.time()
            return False

    def clear(self):
        with self._lock:
            self._seen.clear()
