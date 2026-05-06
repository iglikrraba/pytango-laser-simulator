#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping simulated hardware and device server..."
pkill -f "sim_hw_server.py" || true
pkill -f "laser_diag_ds.py" || true

echo "Stopping TANGO containers..."
newgrp docker -c "docker compose -f '$ROOT_DIR/docker-compose.yml' down"

echo "Project stopped."