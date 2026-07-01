# Driver Model

Drivers are isolated modules responsible for communicating with physical hardware.

Each driver exposes a common interface consisting of:

- initialize()
- start()
- stop()
- status()
- capabilities()
- health()

Drivers publish hardware events to HAL, which distributes them to interested components.

Driver failures are isolated to prevent system-wide crashes.
