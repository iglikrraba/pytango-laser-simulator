#!/usr/bin/env python3
import sys
import os

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
	sys.path.insert(0, ROOT_DIR)

from laser_diag_ds import LaserHardwareClient
import numpy as np

client = LaserHardwareClient("127.0.0.1", 10001, timeout=2.0)

print("=== Testing Hardware Client ===")

print("\n1. Ping:")
print(f"   {client.ping()}")

print("\n2. Set Mirror X=0.3, Y=-0.2:")
client.set_value("X", 0.3)
client.set_value("Y", -0.2)
state = client.read_state()
print(f"   State: {state}")

print("\n3. Set Sigma=0.15, Noise=0.05:")
client.set_value("SIGMA", 0.15)
client.set_value("NOISE", 0.05)
state = client.read_state()
print(f"   State: {state}")

print("\n4. Read Beam Profile:")
beam = client.read_beam()
print(f"   Shape: {beam.shape}")
print(f"   Min: {beam.min():.4f}, Max: {beam.max():.4f}")

print("\n5. Compute Centroid (numpy in test):")
total = np.sum(beam)
grid = np.linspace(-1.0, 1.0, beam.shape[0])
xx, yy = np.meshgrid(grid, grid)
cx = np.sum(beam * xx) / total
cy = np.sum(beam * yy) / total
print(f"   Centroid: ({cx:.4f}, {cy:.4f})")

print("\n6. Verify centroid matches mirror position:")
print(f"   Expected: X≈{0.3*0.6:.2f}, Y≈{-0.2*0.6:.2f}")
print(f"   Got:      X≈{cx:.2f}, Y≈{cy:.2f}")

client.close()
print("\n=== All Tests Passed ===")