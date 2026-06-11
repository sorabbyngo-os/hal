"""
hal/ambient/twin_feeder.py
Feeds ambient observations to digital twin via API.
Work context nodes have TTL — they expire, not permanent.
Pattern nodes are permanent memory.
"""
from __future__ import annotations
import logging, os, time
import requests
from hal.ambient.context_builder import AmbientContext

log = logging.getLogger("hal.ambient.twin")

TWIN_API  = os.getenv("TWIN_API_BASE", "http://localhost:8741")
TWIN_ID   = os.getenv("HAL_TWIN_ID", "")
TIMEOUT   = 3

def _post_memory(twin_id: str, category: str, summary: str,
                 confidence: float = 0.8, expires_in: int = None):
    payload = {"category": category, "summary": summary,
               "confidence": confidence, "source": "hal.ambient"}
    if expires_in:
        payload["expires_at"] = time.time() + expires_in
    try:
        requests.post(f"{TWIN_API}/v1/twins/{twin_id}/memory",
                      json=payload, timeout=TIMEOUT)
    except Exception as e:
        log.debug("twin feed failed: %s", e)

def feed_context(ctx: AmbientContext, twin_id: str):
    """Feed current work context — expires in 1 hour."""
    if not twin_id:
        return
    summary = ctx.summary()
    _post_memory(twin_id, "work_context", summary,
                 confidence=0.75, expires_in=3600)

def feed_pattern(pattern: str, twin_id: str):
    """Feed learned pattern — permanent memory."""
    if not twin_id:
        return
    _post_memory(twin_id, "work_pattern", pattern,
                 confidence=0.90)
