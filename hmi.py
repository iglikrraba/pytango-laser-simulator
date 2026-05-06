#!/usr/bin/env python3
import sys
import os
import numpy as np
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from tango import DeviceProxy

# Ensure TANGO_HOST is set; prefer localhost:10000 for host-based clients
if os.environ.get("TANGO_HOST") not in ("localhost:10000", "127.0.0.1:10000"):
    os.environ["TANGO_HOST"] = "localhost:10000"
    print("Warning: TANGO_HOST set to 'localhost:10000' for host client")

# Avoid invalid font warnings on some systems
qt_font = os.environ.get("QT_QPA_FONT", "")
if not qt_font or "Hack" in qt_font:
    os.environ["QT_QPA_FONT"] = "Sans Serif,10"


class LaserHMI(QtWidgets.QMainWindow):
    def __init__(self, device_name):
        super().__init__()
        self.setWindowTitle("PyTango Laser Diagnostic HMI")
        self._dev = DeviceProxy(device_name)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)

        self._plot = pg.PlotWidget()
        self._plot.setAspectLocked(True)
        self._image = pg.ImageItem()
        self._plot.addItem(self._image)
        layout.addWidget(self._plot, 2)

        controls = QtWidgets.QVBoxLayout()
        layout.addLayout(controls, 1)

        self._x_ctrl = self._make_slider("Mirror X", -1.0, 1.0, 0.001, controls)
        self._y_ctrl = self._make_slider("Mirror Y", -1.0, 1.0, 0.001, controls)
        self._sigma_ctrl = self._make_slider("Sigma", 0.05, 0.6, 0.001, controls)
        self._noise_ctrl = self._make_slider("Noise", 0.0, 0.2, 0.001, controls)

        self._centroid = QtWidgets.QLabel("Centroid: (0.000, 0.000)")
        controls.addWidget(self._centroid)

        self._status = QtWidgets.QLabel("Status: OK")
        controls.addWidget(self._status)
        controls.addStretch()

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._update_beam)
        self._timer.start(200)

        self._write_timer = QtCore.QTimer(self)
        self._write_timer.setSingleShot(True)
        self._write_timer.timeout.connect(self._write_controls)

        self._init_from_device()

    def _make_slider(self, label, minimum, maximum, step, parent_layout):
        box = QtWidgets.QGroupBox(label)
        grid = QtWidgets.QGridLayout(box)
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 1000)
        spin = QtWidgets.QDoubleSpinBox()
        spin.setDecimals(3)
        spin.setSingleStep(step)
        spin.setRange(minimum, maximum)
        grid.addWidget(slider, 0, 0)
        grid.addWidget(spin, 0, 1)
        parent_layout.addWidget(box)

        def to_value(pos):
            return minimum + (maximum - minimum) * (pos / 1000.0)

        def to_pos(value):
            return int(round((value - minimum) / (maximum - minimum) * 1000.0))

        slider.valueChanged.connect(lambda v: spin.setValue(to_value(v)))
        spin.valueChanged.connect(lambda v: slider.setValue(to_pos(v)))
        spin.valueChanged.connect(self._schedule_write)
        return spin

    def _schedule_write(self):
        self._write_timer.start(80)

    def _init_from_device(self):
        try:
            self._x_ctrl.setValue(self._dev.read_attribute("mirror_x").value)
            self._y_ctrl.setValue(self._dev.read_attribute("mirror_y").value)
            self._sigma_ctrl.setValue(self._dev.read_attribute("sigma").value)
            self._noise_ctrl.setValue(self._dev.read_attribute("noise").value)
        except Exception as exc:
            self._status.setText(f"Status: {exc}")

    def _write_controls(self):
        try:
            self._dev.write_attribute("mirror_x", float(self._x_ctrl.value()))
            self._dev.write_attribute("mirror_y", float(self._y_ctrl.value()))
            self._dev.write_attribute("sigma", float(self._sigma_ctrl.value()))
            self._dev.write_attribute("noise", float(self._noise_ctrl.value()))
            self._status.setText("Status: OK")
        except Exception as exc:
            self._status.setText(f"Status: {exc}")

    def _update_beam(self):
        try:
            beam = self._dev.read_attribute("beam_profile").value
            arr = np.array(beam, dtype=np.float64)
            self._image.setImage(arr.T, autoLevels=True)
            centroid = self._dev.read_attribute("beam_centroid").value
            self._centroid.setText(f"Centroid: ({centroid[0]:.3f}, {centroid[1]:.3f})")
            self._status.setText("Status: OK")
        except Exception as exc:
            self._status.setText(f"Status: {exc}")


def main():
    if len(sys.argv) < 2:
        print("Usage: hmi.py <device_name>")
        sys.exit(1)
    app = QtWidgets.QApplication(sys.argv)
    win = LaserHMI(sys.argv[1])
    win.resize(1000, 600)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
