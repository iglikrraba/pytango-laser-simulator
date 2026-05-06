#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed or not in PATH."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required."
  exit 1
fi

if [ ! -d "$ROOT_DIR/venv" ]; then
  echo "Creating venv and installing Python deps..."
  python3 -m venv "$ROOT_DIR/venv"
  "$ROOT_DIR/venv/bin/pip" install --upgrade pip
  "$ROOT_DIR/venv/bin/pip" install -r "$ROOT_DIR/requirements.txt"
fi

export TANGO_HOST=localhost:10000

echo "Starting TANGO containers..."
newgrp docker -c "docker compose -f '$ROOT_DIR/docker-compose.yml' up -d"

export TANGO_HOST=localhost:10000

echo "Starting simulated hardware (TCP server)..."
if ! pgrep -f "sim_hw_server.py" >/dev/null 2>&1; then
  nohup "$ROOT_DIR/venv/bin/python" "$ROOT_DIR/sim_hw_server.py" --port 10001 > /tmp/sim_hw.log 2>&1 &
  echo "Sim HW PID: $!"
fi

echo "Waiting for TANGO DB..."
for i in {1..40}; do
  if nc -z localhost 10000 >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "Waiting for DataBaseds..."
db_ready=0
for i in {1..40}; do
  if newgrp docker -c "docker run --rm --network pytango_default -e TANGO_HOST=databaseds:10000 cpascual/tango-cpp:latest tango_admin --ping-database 2" >/dev/null 2>&1; then
    db_ready=1
    break
  fi
  sleep 0.5
done
if [ "$db_ready" -ne 1 ]; then
  echo "ERROR: DataBaseds not responding. Check container logs."
  exit 1
fi

echo "Registering device server..."
newgrp docker -c "docker run --rm --network pytango_default -e TANGO_HOST=databaseds:10000 cpascual/tango-cpp:latest tango_admin --add-server laser_diag_ds/diag LaserDiagnostic laser/diag/1"

echo "Verifying device registration..."
newgrp docker -c "docker run --rm --network pytango_default -e TANGO_HOST=databaseds:10000 cpascual/tango-cpp:latest tango_admin --check-device laser/diag/1" || true

echo "Registering device properties..."
newgrp docker -c "docker run --rm --network pytango_default -e TANGO_HOST=databaseds:10000 cpascual/tango-cpp:latest tango_admin --add-property laser/diag/1 host 127.0.0.1"
newgrp docker -c "docker run --rm --network pytango_default -e TANGO_HOST=databaseds:10000 cpascual/tango-cpp:latest tango_admin --add-property laser/diag/1 port 10001"


"$ROOT_DIR/venv/bin/python" "$ROOT_DIR/register_device.py"

echo "Starting device server..."
if ! pgrep -f "laser_diag_ds.py" >/dev/null 2>&1; then
  export TANGO_SERVER_HOST="$(hostname)"
  nohup "$ROOT_DIR/venv/bin/python" "$ROOT_DIR/laser_diag_ds.py" diag > /tmp/laser_diag_ds.log 2>&1 &
  echo "Device server PID: $!"
fi

echo "Project started."
echo "Launch GUI with: $ROOT_DIR/venv/bin/python $ROOT_DIR/hmi.py laser/diag/1"
