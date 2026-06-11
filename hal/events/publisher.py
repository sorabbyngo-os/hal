"""
hal/events/publisher.py
Publishes HAL events to chameha event bus via NATS.
Falls back to HTTP if NATS unavailable.
"""
from __future__ import annotations
import asyncio, json, logging, os, threading
from hal.events.normalizer import HALEvent

log = logging.getLogger("hal.events.publisher")

NATS_URL   = os.getenv("NATS_URL", "nats://localhost:4222")
NATS_SUBJ  = "sorabbyngo.hal.events"

class EventPublisher:
    def __init__(self):
        self._nc        = None
        self._loop      = asyncio.new_event_loop()
        self._thread    = threading.Thread(
            target=self._loop.run_forever, daemon=True)
        self._thread.start()
        asyncio.run_coroutine_threadsafe(self._connect(), self._loop)

    async def _connect(self):
        try:
            import nats
            self._nc = await nats.connect(NATS_URL)
            log.info("HAL publisher connected to NATS: %s", NATS_URL)
        except Exception as e:
            log.warning("NATS unavailable (%s) — events logged only", e)

    def publish(self, event: HALEvent):
        """Publish event — fire and forget."""
        asyncio.run_coroutine_threadsafe(
            self._publish(event), self._loop)

    async def _publish(self, event: HALEvent):
        payload = json.dumps(event.to_dict()).encode()
        if self._nc and self._nc.is_connected:
            try:
                await self._nc.publish(NATS_SUBJ, payload)
                log.debug("published [%s] %s", event.severity.value,
                          event.message[:60])
                return
            except Exception as e:
                log.warning("NATS publish failed: %s", e)
        # Fallback: log only
        log.info("HAL EVENT [%s][%s] %s",
                 event.source, event.severity.value, event.message)

    def close(self):
        if self._nc:
            asyncio.run_coroutine_threadsafe(
                self._nc.close(), self._loop)
