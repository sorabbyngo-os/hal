#!/usr/bin/env python3
"""
main.py — Sorabbyngo HAL daemon
Polls all sensors, normalizes to events, publishes to chameha + NATS.
Runs every HAL_PUBLISH_INTERVAL seconds (default: 30).
"""
import logging, os, signal, time, sys

logging.basicConfig(
    level=os.getenv("HAL_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger("hal.main")

from hal.sensors import thermal, battery, memory, cpu, storage, network
from hal.events.normalizer import (
    from_thermal, from_battery, from_memory, from_storage, from_network
)
from hal.events.deduplicator import Deduplicator
from hal.events.publisher import EventPublisher
from hal.ambient.context_builder import build as build_context
from hal.ambient.twin_feeder import feed_context
from hal.kernel.nodeid_reader import read_node_id

INTERVAL  = int(os.getenv("HAL_PUBLISH_INTERVAL", "30"))
TWIN_ID   = os.getenv("HAL_TWIN_ID", "")

_running  = True

def _stop(sig, frame):
    global _running
    log.info("HAL stopping (signal %d)", sig)
    _running = False

signal.signal(signal.SIGTERM, _stop)
signal.signal(signal.SIGINT,  _stop)

def poll():
    dedup     = Deduplicator()
    publisher = EventPublisher()
    node_id   = read_node_id()
    log.info("HAL started — NodeID: %s...", node_id[:12])
    log.info("Polling interval: %ds", INTERVAL)

    while _running:
        try:
            # Read all sensors
            t_state = thermal.read()
            b_state = battery.read()
            m_state = memory.read()
            s_state = storage.read()
            n_state = network.read()

            # Normalize to events
            events = [
                from_thermal(t_state),
                from_battery(b_state),
                from_memory(m_state),
                from_storage(s_state),
                from_network(n_state),
            ]

            # Publish non-duplicate events
            for event in events:
                if event and not dedup.is_duplicate(event):
                    publisher.publish(event)

            # Ambient context snapshot
            ctx = build_context()
            if TWIN_ID:
                feed_context(ctx, TWIN_ID)

            log.debug("Poll complete: %s", ctx.summary())

        except Exception as e:
            log.error("Poll error: %s", e, exc_info=True)

        time.sleep(INTERVAL)

    publisher.close()
    log.info("HAL stopped")

if __name__ == "__main__":
    poll()
