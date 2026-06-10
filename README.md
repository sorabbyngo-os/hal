<div align="center">
<br/>

# hal

### Hardware Abstraction Layer — sensor bridge, device events, and ambient awareness feed for Chameha and Byngox.

<br/>

[![Division](https://img.shields.io/badge/Division-Sorabbyngo_OS-6C3FC4?style=for-the-badge)](https://github.com/sorabbyngo-os)
[![Lang](https://img.shields.io/badge/Lang-Rust-AA66FF?style=for-the-badge)](https://github.com/sorabbyngo-os/hal)
[![Status](https://img.shields.io/badge/Status-In_Development-FF6B35?style=for-the-badge)](https://github.com/sorabbyngo-os/hal)

</div>

---

## What It Does

hal is the hardware abstraction layer that bridges physical sensors and devices to the Sorabbyngo OS software stack. It normalises raw hardware events — camera frames, microphone input, IMU data, ambient light, location, battery — into a unified event stream consumed by Chameha (voice), Byngox (agents), and the wayland-shell (UI).

---

## Features

| Feature | Description |
|---|---|
| **Sensor Bridge** | Normalises input from camera, mic, IMU, GPS, ambient light, proximity |
| **Ambient Awareness Feed** | Continuous context stream for Byngox agents |
| **Device Events** | USB hotplug, display connect/disconnect, power state changes |
| **Camera Pipeline** | V4L2 capture, format negotiation, frame delivery to Chameha/agents |
| **Audio Pipeline** | PipeWire integration — mic capture, speaker output, routing |
| **Location Service** | GPS + network location, offline geofencing |
| **Battery & Power** | Power state, charge level, thermal status |

---

## Architecture

```
hal/
├── src/
│   ├── sensors/      # Sensor abstraction (camera, mic, IMU, GPS, light)
│   ├── events/       # Hardware event bus
│   ├── camera/       # V4L2 camera pipeline
│   ├── audio/        # PipeWire audio pipeline
│   ├── location/     # GPS + network location service
│   ├── power/        # Battery, thermal, power state
│   └── ambient/      # Ambient awareness feed compositor
├── Cargo.toml
└── README.md
```

---

## Ambient Awareness Feed

The ambient feed is a continuous JSON-L stream published to Byngox and subscribed to by any agent that needs environmental context:

```json
{"ts": 1748736000, "type": "location", "lat": -0.6800, "lon": 37.1500, "acc": 5}
{"ts": 1748736001, "type": "ambient_light", "lux": 420, "condition": "indoor"}
{"ts": 1748736002, "type": "audio", "event": "voice_activity_detected"}
{"ts": 1748736003, "type": "power", "battery": 73, "charging": false, "thermal": "nominal"}
```

---

## Stack

- **Language:** Rust
- **Camera:** V4L2 (linux-videodev2)
- **Audio:** PipeWire
- **Location:** gpsd / NetworkManager
- **OS target:** byngo-os, novela-os, edge-os

---

*Sorabbyngo OS · Kisii, Kenya · 2026*
