#!/usr/bin/env python3
import argparse
import socketserver
import threading
import numpy as np


class LaserSimState:
    def __init__(self, size=64, sigma=0.2, noise=0.02):
        self.size = int(size)
        self._lock = threading.Lock()
        self._x = 0.0
        self._y = 0.0
        self._sigma = float(sigma)
        self._noise = float(noise)
        self._grid = np.linspace(-1.0, 1.0, self.size)
        self._xx, self._yy = np.meshgrid(self._grid, self._grid)

    def set_mirror(self, x=None, y=None):
        with self._lock:
            if x is not None:
                self._x = float(x)
            if y is not None:
                self._y = float(y)

    def set_sigma(self, sigma):
        sigma = float(sigma)
        if sigma <= 0.0:
            raise ValueError("sigma must be > 0")
        with self._lock:
            self._sigma = sigma

    def set_noise(self, noise):
        noise = float(noise)
        if noise < 0.0:
            raise ValueError("noise must be >= 0")
        with self._lock:
            self._noise = noise

    def get_state(self):
        with self._lock:
            return self._x, self._y, self._sigma, self._noise

    def generate_beam(self):
        x, y, sigma, noise = self.get_state()
        cx = x * 0.6
        cy = y * 0.6
        gauss = np.exp(-((self._xx - cx) ** 2 + (self._yy - cy) ** 2) / (2 * sigma**2))
        beam = gauss + noise * np.random.randn(self.size, self.size)
        return np.clip(beam, 0.0, None)


class LaserSimTCPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            line = self.rfile.readline()
            if not line:
                break
            cmd = line.decode("ascii", errors="ignore").strip()
            if not cmd:
                continue
            response = self.server.process_command(cmd)
            self.wfile.write((response + "\n").encode("ascii"))
            self.wfile.flush()


class LaserSimTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, handler_class, state):
        super().__init__(server_address, handler_class)
        self.state = state

    def process_command(self, line):
        try:
            tokens = line.split()
            if not tokens:
                return "ERR empty"
            op = tokens[0].upper()
            if op == "PING":
                return "OK PONG"
            if op == "SET":
                if len(tokens) != 3:
                    return "ERR usage: SET <X|Y|SIGMA|NOISE> <value>"
                target = tokens[1].upper()
                value = float(tokens[2])
                if target == "X":
                    self.state.set_mirror(x=value)
                elif target == "Y":
                    self.state.set_mirror(y=value)
                elif target == "SIGMA":
                    self.state.set_sigma(value)
                elif target == "NOISE":
                    self.state.set_noise(value)
                else:
                    return "ERR unknown SET target"
                return "OK"
            if op == "READ":
                if len(tokens) != 2:
                    return "ERR usage: READ <BEAM|STATE>"
                target = tokens[1].upper()
                if target == "STATE":
                    x, y, sigma, noise = self.state.get_state()
                    return (
                        f"STATE X {x:.6f} Y {y:.6f} "
                        f"SIGMA {sigma:.6f} NOISE {noise:.6f}"
                    )
                if target == "BEAM":
                    beam = self.state.generate_beam()
                    rows, cols = beam.shape
                    data = " ".join(f"{v:.6f}" for v in beam.ravel())
                    return f"BEAM {rows} {cols} {data}"
                return "ERR unknown READ target"
            return "ERR unknown command"
        except Exception as exc:
            return f"ERR {exc}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=10001)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--sigma", type=float, default=0.2)
    parser.add_argument("--noise", type=float, default=0.02)
    args = parser.parse_args()

    state = LaserSimState(size=args.size, sigma=args.sigma, noise=args.noise)
    server = LaserSimTCPServer((args.host, args.port), LaserSimTCPHandler, state)
    print(f"Sim HW server on {args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
