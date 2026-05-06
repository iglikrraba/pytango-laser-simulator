#!/usr/bin/env python3
import sys
import os

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Test the core LaserDiagnostic class functionality without running as a TANGO device server
from laser_diag_ds import LaserHardwareClient
import numpy as np
import time

def test_core_functionality():
    print("Testing core LaserDiagnostic functionality (via LaserHardwareClient)...")
    
    # Create a client instance
    client = LaserHardwareClient('127.0.0.1', 10001, timeout=2.0)
    
    # Test 1: Ping
    print("\n1. Testing ping:")
    try:
        result = client.ping()
        print(f"   Ping result: {result}")
    except Exception as e:
        print(f"   Ping failed: {e}")
        client.close()
        return False
    
    # Test 2: Set and get state
    print("\n2. Testing state setting/getting:")
    try:
        client.set_value("X", 0.5)
        client.set_value("Y", -0.3)
        client.set_value("SIGMA", 0.15)
        client.set_value("NOISE", 0.02)
        
        state = client.read_state()
        print(f"   State: {state}")
        
        expected = {'X': 0.5, 'Y': -0.3, 'SIGMA': 0.15, 'NOISE': 0.02}
        for key, value in expected.items():
            if abs(state.get(key, 0) - value) > 0.000001:
                print(f"   ERROR: State mismatch for {key}: expected {value}, got {state.get(key)}")
                client.close()
                return False
        print("   State test passed")
    except Exception as e:
        print(f"   State test failed: {e}")
        client.close()
        return False
    
    # Test 3: Read beam profile
    print("\n3. Testing beam profile reading:")
    try:
        beam = client.read_beam()
        print(f"   Beam shape: {beam.shape}")
        print(f"   Beam dtype: {beam.dtype}")
        print(f"   Beam min: {beam.min():.6f}")
        print(f"   Beam max: {beam.max():.6f}")
        print(f"   Beam mean: {beam.mean():.6f}")
        
        if beam.shape != (64, 64):
            print(f"   ERROR: Expected beam shape (64, 64), got {beam.shape}")
            client.close()
            return False
            
        if beam.dtype != np.float64:
            print(f"   ERROR: Expected beam dtype float64, got {beam.dtype}")
            client.close()
            return False
            
        print("   Beam profile test passed")
    except Exception as e:
        print(f"   Beam profile test failed: {e}")
        client.close()
        return False
    
    # Test 4: Compute centroid (mirroring the device server logic)
    print("\n4. Testing centroid calculation:")
    try:
        beam = client.read_beam()
        total = np.sum(beam)
        if total <= 0.0:
            centroid = np.array([0.0, 0.0], dtype=np.float64)
        else:
            grid = np.linspace(-1.0, 1.0, beam.shape[0])
            xx, yy = np.meshgrid(grid, grid)
            cx = np.sum(beam * xx) / total
            cy = np.sum(beam * yy) / total
            centroid = np.array([float(cx), float(cy)], dtype=np.float64)
        
        print(f"   Centroid: [{centroid[0]:.6f}, {centroid[1]:.6f}]")
        print("   Centroid test passed")
    except Exception as e:
        print(f"   Centroid test failed: {e}")
        client.close()
        return False
    
    client.close()
    print("\nAll core functionality tests passed!")
    return True

if __name__ == "__main__":
    success = test_core_functionality()
    sys.exit(0 if success else 1)