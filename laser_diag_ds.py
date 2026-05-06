#!/usr/bin/env python3
import os
import socket
import threading
import time
import numpy as np
import tango
from tango import DevState
from tango.server import Device, attribute, command, device_property, run


class LaserHardwareClient:
    def __init__(self, host, port, timeout=2.0):
        self.host = host
        self.port = int(port)
        self.timeout = float(timeout)
        self._lock = threading.Lock()
        self._sock = None
        self._file = None

    def _connect(self):
        if self._sock:
            return
        self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self._file = self._sock.makefile("rwb")

    def _send(self, line):
        self._file.write((line + "\n").encode("ascii"))
        self._file.flush()
        resp = self._file.readline()
        if not resp:
            raise ConnectionError("No response from hardware")
        text = resp.decode("ascii", errors="ignore").strip()
        if text.startswith("ERR"):
            raise RuntimeError(text)
        return text

    def request(self, line):
        with self._lock:
            try:
                self._connect()
                return self._send(line)
            except Exception:
                self.close()
                self._connect()
                return self._send(line)

    def close(self):
        if self._file:
            try:
                self._file.close()
            except Exception:
                pass
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        self._file = None
        self._sock = None

    def ping(self):
        return self.request("PING")

    def set_value(self, target, value):
        self.request(f"SET {target} {value:.6f}")

    def read_state(self):
        resp = self.request("READ STATE")
        tokens = resp.split()
        if not tokens or tokens[0] != "STATE":
            raise RuntimeError("Invalid STATE response")
        if (len(tokens) - 1) % 2 != 0:
            raise RuntimeError("Malformed STATE response")
        data = {}
        for i in range(1, len(tokens), 2):
            key = tokens[i].upper()
            data[key] = float(tokens[i + 1])
        return data

    def read_beam(self):
        resp = self.request("READ BEAM")
        parts = resp.split(maxsplit=3)
        if len(parts) < 4 or parts[0] != "BEAM":
            raise RuntimeError("Invalid BEAM response")
        rows = int(parts[1])
        cols = int(parts[2])
        data = np.fromstring(parts[3], sep=" ", dtype=np.float64)
        if data.size != rows * cols:
            raise RuntimeError("Invalid BEAM data length")
        return data.reshape(rows, cols)


class LaserDiagnostic(Device):
    host = device_property(dtype=str, default_value="127.0.0.1")
    port = device_property(dtype=int, default_value=10001)
    timeout = device_property(dtype=float, default_value=2.0)
    cache_ttl = device_property(dtype=float, default_value=0.2)


    def init_device(self):
        super().init_device()
        self._client = LaserHardwareClient(self.host, self.port, self.timeout)
        self._state_cache = None
        self._state_cache_ts = 0.0
        self._beam_cache = None
        self._beam_cache_ts = 0.0
        self.set_state(DevState.ON)
        self.set_status("Ready")

    def _get_state(self):
        now = time.time()
        if self._state_cache and (now - self._state_cache_ts) < self.cache_ttl:
            return self._state_cache
        self._state_cache = self._client.read_state()
        self._state_cache_ts = now
        return self._state_cache

    def _get_beam(self):
        now = time.time()
        if self._beam_cache is not None and (now - self._beam_cache_ts) < self.cache_ttl:
            return self._beam_cache
        self._beam_cache = self._client.read_beam()
        self._beam_cache_ts = now
        return self._beam_cache

    @attribute(dtype=float, access=tango.AttrWriteType.READ_WRITE)
    def mirror_x(self):
        return self._get_state().get("X", 0.0)

    @mirror_x.write
    def mirror_x(self, value):
        self._client.set_value("X", float(value))
        self._state_cache = None

    @attribute(dtype=float, access=tango.AttrWriteType.READ_WRITE)
    def mirror_y(self):
        return self._get_state().get("Y", 0.0)

    @mirror_y.write
    def mirror_y(self, value):
        self._client.set_value("Y", float(value))
        self._state_cache = None

    @attribute(dtype=float, access=tango.AttrWriteType.READ_WRITE)
    def sigma(self):
        return self._get_state().get("SIGMA", 0.0)

    @sigma.write
    def sigma(self, value):
        self._client.set_value("SIGMA", float(value))
        self._state_cache = None

    @attribute(dtype=float, access=tango.AttrWriteType.READ_WRITE)
    def noise(self):
        return self._get_state().get("NOISE", 0.0)

    @noise.write
    def noise(self, value):
        self._client.set_value("NOISE", float(value))
        self._state_cache = None

    @attribute(
        dtype=((float,),),
        max_dim_x=64,
        max_dim_y=64,
    )
    def beam_profile(self):
        beam = self._get_beam()
        return beam.astype(float, copy=False)

    @attribute(
        dtype=(float,),
        max_dim_x=2,
    )
    def beam_centroid(self):
        beam = self._get_beam()
        total = np.sum(beam)
        if total <= 0.0:
            return np.array([0.0, 0.0], dtype=np.float64)
        grid = np.linspace(-1.0, 1.0, beam.shape[0])
        xx, yy = np.meshgrid(grid, grid)
        cx = np.sum(beam * xx) / total
        cy = np.sum(beam * yy) / total
        return np.array([float(cx), float(cy)], dtype=np.float64)

    @command
    def Ping(self):
        return self._client.ping()


if __name__ == "__main__":
    if "TANGO_SERVER_HOST" not in os.environ:
        os.environ["TANGO_SERVER_HOST"] = socket.gethostname()
    run([LaserDiagnostic])
