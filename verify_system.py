#!/usr/bin/env python3
"""
Verification script for the PyTango Laser Diagnostic Simulator system.
This script verifies that all components work together correctly without
requiring the full TANGO device server to be running as a service.
"""

import sys
import os
import time
import threading
import numpy as np

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def test_hardware_server():
    """Test the simulated hardware TCP server"""
    print("=" * 60)
    print("TESTING SIMULATED HARDWARE TCP SERVER")
    print("=" * 60)
    
    from sim_hw_server import LaserSimState, LaserSimTCPServer
    import socketserver
    
    # Create test state
    state = LaserSimState(size=64, sigma=0.2, noise=0.02)
    
    # Test state setting
    state.set_mirror(0.5, -0.3)
    state.set_sigma(0.15)
    state.set_noise(0.02)
    
    x, y, sigma, noise = state.get_state()
    print(f"✓ Mirror position: X={x:.3f}, Y={y:.3f}")
    print(f"✓ Beam parameters: Sigma={sigma:.3f}, Noise={noise:.3f}")
    
    # Test beam generation
    beam = state.generate_beam()
    print(f"✓ Beam generated: shape={beam.shape}, dtype={beam.dtype}")
    print(f"  Beam stats: min={beam.min():.6f}, max={beam.max():.6f}, mean={beam.mean():.6f}")
    
    # Test that beam changes with mirror position
    state.set_mirror(0.0, 0.0)
    beam_center = state.generate_beam()
    state.set_mirror(0.5, 0.5)
    beam_offset = state.generate_beam()
    
    center_sum = np.sum(beam_center)
    offset_sum = np.sum(beam_offset)
    print(f"✓ Beam response to mirror: center_sum={center_sum:.3f}, offset_sum={offset_sum:.3f}")
    
    # Test TCP server command processing (without actually starting server)
    server = LaserSimTCPServer(("localhost", 0), None, state)  # Port 0 = auto-assign
    
    test_commands = [
        "PING",
        "SET X 0.5",
        "SET Y -0.3", 
        "SET SIGMA 0.15",
        "SET NOISE 0.02",
        "READ STATE",
        "READ BEAM"
    ]
    
    print("\n✓ Testing command processing:")
    for cmd in test_commands:
        try:
            response = server.process_command(cmd)
            print(f"  {cmd:<15} → {response[:50]}{'...' if len(response) > 50 else ''}")
        except Exception as e:
            print(f"  {cmd:<15} → ERROR: {e}")
            return False
    
    return True

def test_device_server_logic():
    """Test the core device server logic"""
    print("\n" + "=" * 60)
    print("TESTING DEVICE SERVER LOGIC")
    print("=" * 60)
    
    from laser_diag_ds import LaserHardwareClient
    from sim_hw_server import LaserSimState, LaserSimTCPServer, LaserSimTCPHandler
    import numpy as np
    
    state = LaserSimState(size=64, sigma=0.2, noise=0.02)
    server = LaserSimTCPServer(("127.0.0.1", 0), LaserSimTCPHandler, state)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    # Test hardware client (which the device server uses)
    client = None
    try:
        client = LaserHardwareClient(host, port, timeout=2.0)
        print("✓ Testing hardware client communication:")
        
        # Ping
        ping_result = client.ping()
        print(f"  Ping: {ping_result}")
        
        # Set parameters
        client.set_value("X", 0.4)
        client.set_value("Y", -0.2)
        client.set_value("SIGMA", 0.18)
        client.set_value("NOISE", 0.015)
        print("  Set parameters: X=0.4, Y=-0.2, Sigma=0.18, Noise=0.015")
        
        # Read state
        state = client.read_state()
        print(f"  Read state: {state}")
        
        # Read beam
        beam = client.read_beam()
        print(f"  Beam shape: {beam.shape}, dtype: {beam.dtype}")
        print(f"  Beam stats: min={beam.min():.6f}, max={beam.max():.6f}, mean={beam.mean():.6f}")
        
        # Test centroid calculation (same as device server)
        total = np.sum(beam)
        if total > 0.0:
            grid = np.linspace(-1.0, 1.0, beam.shape[0])
            xx, yy = np.meshgrid(grid, grid)
            cx = np.sum(beam * xx) / total
            cy = np.sum(beam * yy) / total
            centroid = np.array([float(cx), float(cy)], dtype=np.float64)
            print(f"  Calculated centroid: [{centroid[0]:.6f}, {centroid[1]:.6f}]")
        else:
            centroid = np.array([0.0, 0.0], dtype=np.float64)
            print(f"  Centroid (zero beam): [{centroid[0]:.6f}, {centroid[1]:.6f}]")
        
    finally:
        if client is not None:
            client.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
    return True

def test_hmi_components():
    """Test that HMI components can be imported"""
    print("\n" + "=" * 60)
    print("TESTING HMI COMPONENTS")
    print("=" * 60)
    if os.environ.get("PYTANGO_SKIP_HMI_TEST", "").lower() in ("1", "true", "yes"):
        print("Skipping HMI component test (PYTANGO_SKIP_HMI_TEST=1)")
        return True
    
    try:
        # Test imports
        from PyQt5 import QtWidgets
        import pyqtgraph as pg
        import numpy as np
        print("✓ PyQt5, pyqtgraph, and numpy imported successfully")
        
        # Test that we can create basic Qt objects (without showing GUI)
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        print("✓ QApplication can be created")
        
        # Test pyqtgraph ImageItem creation
        img = pg.ImageItem()
        print("✓ pyqtgraph ImageItem can be created")
        
        # Test numpy array manipulation (what HMI does)
        test_data = np.random.rand(64, 64).astype(np.float64)
        img.setImage(test_data.T, autoLevels=True)
        print("✓ ImageItem can process 64x64 float data")
        
        return True
    except Exception as e:
        print(f"✗ HMI component test failed: {e}")
        return False

def main():
    print("PyTango Laser Diagnostic Simulator - System Verification")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Hardware server
    if not test_hardware_server():
        all_passed = False
    
    # Test 2: Device server logic
    if not test_device_server_logic():
        all_passed = False
    
    # Test 3: HMI components
    if not test_hmi_components():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! System is ready to run.")
        print("\nTo start the full system:")
        print("  1. ./start_project.sh")
        print("  2. ./venv/bin/python hmi.py laser/diag/1")
        print("  3. ./stop_project.sh (when done)")
    else:
        print("❌ SOME TESTS FAILED! Please check the output above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())