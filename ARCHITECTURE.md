# Architecture

## Overview
This project implements a small three-tier control stack around a simulated laser diagnostic device. The simulator models a Gaussian beam and exposes a simple TCP protocol. The PyTango device server adapts that protocol into attributes and commands, and the HMI renders the beam in real time.

```
Simulated Hardware (TCP) <-> PyTango Device Server <-> HMI (PyQt5)
             |                          |
             +-------- TANGO DB --------+
```

## Components

### Hardware simulator
- Implementation: [sim_hw_server.py](sim_hw_server.py)
- TCP server with a lightweight command parser.
- Generates a 2D Gaussian beam with controllable noise and width.

**Protocol**
- `PING` -> `OK PONG`
- `SET X|Y|SIGMA|NOISE <value>` -> `OK`
- `READ STATE` -> `STATE X <x> Y <y> SIGMA <s> NOISE <n>`
- `READ BEAM` -> `BEAM <rows> <cols> <flat-data...>`

### PyTango device server
- Implementation: [laser_diag_ds.py](laser_diag_ds.py)
- Attributes: `mirror_x`, `mirror_y`, `sigma`, `noise`, `beam_profile`, `beam_centroid`
- Command: `Ping`
- The `LaserHardwareClient` manages TCP communication and retries on errors.
- `cache_ttl` is used to reduce socket reads when the HMI is polling.

### HMI
- Implementation: [hmi.py](hmi.py)
- Polls the device server every 200 ms and renders the beam with pyqtgraph.
- Sliders write mirror position, sigma, and noise back to the device server.
- Displays the beam centroid as a quick alignment indicator.

## Data flow
1. The HMI writes mirror and beam parameters to the device server.
2. The device server sends `SET` commands to the simulator.
3. The HMI reads `beam_profile` and `beam_centroid` attributes.
4. The device server fetches data from the simulator via `READ` commands.

## Operational defaults
- TANGO database: `localhost:10000`
- Simulator: `127.0.0.1:10001`
- Default device name: `laser/diag/1`

## Extensibility
- Replace the simulator with real hardware by implementing the same TCP protocol.
- Increase the beam resolution by raising the simulator grid size and matching the device server limits.
- Add new attributes (e.g., beam energy) by extending both the simulator and device server.
