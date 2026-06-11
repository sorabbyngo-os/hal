"""
hal/events/publisher.py
Publishes HAL events to chameha via NATS.
Tries once on start — stays silent if NATS unavailable.
Falls back to structured logging only.
"""
from __future__ import annotations
import asyncio, json, logging, os, threading
from hal.events.normalizer import HALEvent

log = logging.getLogger("hal.events.publisher")

NATS_URL  = os.getenv("NATS_URL", "nats://localhost:4222")
NATS_SUBJ = "sorabbyngo.hal.events"

class EventPublisher:
    def __init__(self):
        self._nc      = None
        self._online  = False
        self._loop    = asyncio.new_event_loop()
        self._thread  = threading.Thread(
            target=self._loop.run_forever, daemon=True)
        self._thread.start()
        # Try once — don't retry on failure
        fut = asyncio.run_coroutine_threadsafe(self._connect(), self._loop)
        try:
            fut.result(timeout=3)
        except Exception:
            pass

    async def _connect(self):
        try:
            import nats
            self._nc     = await nats.connect(
                NATS_URL,
                connect_timeout=2,
                max_reconnect_attempts=0,   # no retries
            )
            self._online = True
            log.info("HAL publisher connected to NATS: %s", NATS_URL)
        except Exception as e:
            self._online = False
            log.info("NATS unavailable — HAL running in log-only mode (%s)", e)

    def publish(self, event: HALEvent):
        if self._online:
            asyncio.run_coroutine_threadsafe(
                self._publish_nats(event), self._loop)
        else:
            self._publish_log(event)

    async def _publish_nats(self, event: HALEvent):
        try:
            payload = json.dumps(event.to_dict()).encode()
            await self._nc.publish(NATS_SUBJ, payload)
            log.debug("→ NATS [%s] %s", event.severity.value, event.message[:60])
        except Exception as e:
            self._online = False
            log.warning("NATS publish failed — switching to log-only: %s", e)
            self._publish_log(event)

    def _publish_log(self, event: HALEvent):
        log.info("HAL EVENT [%s][%s] %s",
                 event.source, event.severity.value, event.message)

    def close(self):
        if self._nc and self._online:
            asyncio.run_coroutine_threadsafe(
                self._nc.close(), self._loop)
