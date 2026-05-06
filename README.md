# PyTango Laser Diagnostic Simulator

A small, self-contained control stack that simulates a laser diagnostic device using PyTango, a TCP hardware simulator, and a PyQt5 HMI.

## What it does
- Simulates hardware behavior with a simple TCP protocol and Gaussian beam model.
- Exposes the device via a PyTango device server with read/write attributes.
- Displays a live beam profile and centroid in a desktop HMI.
- Uses Docker to run the TANGO database locally.

## Architecture

```
Simulated Hardware (TCP) <-> PyTango Device Server <-> HMI (PyQt5)
             |                          |
             +-------- TANGO DB --------+
```

Detailed design notes are in [ARCHITECTURE.md](ARCHITECTURE.md).

## Quickstart (Linux)

1. Start the stack:

```
./start_project.sh
```

The script creates a virtual environment and installs dependencies from
[requirements.txt](requirements.txt) on first run.

2. Launch the HMI:

```
./venv/bin/python hmi.py laser/diag/1
```

3. Stop everything:

```
./stop_project.sh
```

## Verification (headless-friendly)

Run the integration checks without showing the GUI:

```
PYTANGO_SKIP_HMI_TEST=1 ./venv/bin/python verify_system.py
```

## Requirements
- Python 3.8+
- Docker + Docker Compose
- Linux host (tested with local Docker engine)

## Configuration notes
- `TANGO_HOST` defaults to `localhost:10000` for host-based clients.
- The simulator listens on `127.0.0.1:10001` by default.
- Default device name: `laser/diag/1`.

## Project structure
- [hmi.py](hmi.py) - PyQt5 user interface and live plot.
- [laser_diag_ds.py](laser_diag_ds.py) - PyTango device server and beam/centroid attributes.
- [sim_hw_server.py](sim_hw_server.py) - TCP hardware simulator with Gaussian beam model.
- [register_device.py](register_device.py) - Registers the device and properties in the TANGO DB.
- [verify_system.py](verify_system.py) - End-to-end verification without the full TANGO service.
- [start_project.sh](start_project.sh) and [stop_project.sh](stop_project.sh) - Start and stop scripts.

## License
MIT. See [LICENSE](LICENSE).
