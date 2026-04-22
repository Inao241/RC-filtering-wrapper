import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSlider, QGroupBox, QGridLayout,
                             QPushButton, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPainter, QColor, QPen

class ConfigSignals(QObject):
    config_changed = Signal(dict)
    hidhide_toggle_cloak = Signal(bool)
    hidhide_whitelist_self = Signal()
    hidhide_auto_setup = Signal()

class ControlSlider(QWidget):
    # ... (existing ControlSlider code)
    def __init__(self, label, min_val, max_val, default, decimals=2):
        super().__init__()
        self.decimals = decimals
        self.scale = 10**decimals
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl = QLabel(f"{label}:")
        self.lbl.setMinimumWidth(100)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min_val * self.scale)
        self.slider.setMaximum(max_val * self.scale)
        self.slider.setValue(default * self.scale)
        
        self.val_lbl = QLabel(f"{default:.{decimals}f}")
        self.val_lbl.setMinimumWidth(40)
        
        layout.addWidget(self.lbl)
        layout.addWidget(self.slider)
        layout.addWidget(self.val_lbl)
        
        self.slider.valueChanged.connect(self._on_value_changed)
        
    def _on_value_changed(self, val):
        float_val = val / self.scale
        self.val_lbl.setText(f"{float_val:.{self.decimals}f}")
        
    def value(self):
        return self.slider.value() / self.scale

class JoystickDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(150, 150)
        self.pos_x = 0.0
        self.pos_y = 0.0

    def update_pos(self, x, y):
        self.pos_x = x
        self.pos_y = y
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        w, h = self.width(), self.height()
        center_x, center_y = w / 2, h / 2
        radius = min(w, h) / 2 - 10
        
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw axes
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawLine(center_x - radius, center_y, center_x + radius, center_y)
        painter.drawLine(center_x, center_y - radius, center_x, center_y + radius)
        
        # Draw stick position
        stick_x = center_x + self.pos_x * radius
        stick_y = center_y - self.pos_y * radius # Invert Y for drawing
        
        # Draw line from center to stick
        painter.setPen(QPen(QColor(0, 120, 215, 150), 2)) # Semi-transparent blue line
        painter.drawLine(center_x, center_y, stick_x, stick_y)
        
        # Draw stick indicator (smaller dot)
        painter.setBrush(QColor(0, 120, 215))
        painter.setPen(QPen(QColor(255, 255, 255), 1)) # White border for visibility
        painter.drawEllipse(stick_x - 4, stick_y - 4, 8, 16 if False else 8) # Smaller dot (radius 4)

class RCFilterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DualSense Edge RC Filter Tuner")
        self.setMinimumWidth(600)
        
        self.signals = ConfigSignals()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- Filter Parameters ---
        filter_group = QGroupBox("Filter Parameters (Universal)")
        filter_layout = QVBoxLayout(filter_group)
        
        self.deadzone = ControlSlider("Deadzone (%)", 0, 50, 0, 1) 
        self.anti_deadzone = ControlSlider("Anti-Deadzone (%)", 0, 50, 0, 1)
        self.k_low = ControlSlider("K Low (Stick Center)", 0, 20, 2, 2) 
        self.k_high = ControlSlider("K High (Stick Outer)", 0, 20, 0, 2)
        self.smoothing = ControlSlider("Noise Smoothing", 0, 100, 50, 1) # 0 to 1.0
        
        filter_layout.addWidget(self.deadzone)
        filter_layout.addWidget(self.anti_deadzone)
        filter_layout.addWidget(self.k_low)
        filter_layout.addWidget(self.k_high)
        filter_layout.addWidget(self.smoothing)
        
        main_layout.addWidget(filter_group)
        
        # --- Visualizer ---
        viz_group = QGroupBox("Live Input Monitor")
        viz_layout = QHBoxLayout(viz_group)
        
        l_container = QVBoxLayout()
        self.l_display = JoystickDisplay()
        self.l_label = QLabel("Left Stick")
        self.l_label.setAlignment(Qt.AlignCenter)
        l_container.addWidget(self.l_label)
        l_container.addWidget(self.l_display)
        
        r_container = QVBoxLayout()
        self.r_display = JoystickDisplay()
        self.r_label = QLabel("Right Stick")
        self.r_label.setAlignment(Qt.AlignCenter)
        r_container.addWidget(self.r_label)
        r_container.addWidget(self.r_display)
        
        viz_layout.addLayout(l_container)
        viz_layout.addLayout(r_container)
        
        main_layout.addWidget(viz_group)
        
        # --- HidHide Control ---
        self.hh_group = QGroupBox("HidHide (Exclusive Mode)")
        hh_layout = QHBoxLayout(self.hh_group)
        
        self.hh_status = QLabel("Status: Unknown")
        self.cloak_cb = QCheckBox("Enable Cloaking")
        self.whitelist_btn = QPushButton("Whitelist Current App")
        self.auto_btn = QPushButton("Auto-Hide DualSense")
        
        hh_layout.addWidget(self.hh_status)
        hh_layout.addWidget(self.cloak_cb)
        hh_layout.addWidget(self.whitelist_btn)
        hh_layout.addWidget(self.auto_btn)
        
        main_layout.addWidget(self.hh_group)
        
        # Connect HidHide signals
        self.cloak_cb.clicked.connect(lambda checked: self.signals.hidhide_toggle_cloak.emit(checked))
        self.whitelist_btn.clicked.connect(self.signals.hidhide_whitelist_self.emit)
        self.auto_btn.clicked.connect(self.signals.hidhide_auto_setup.emit)

        self.timer = QTimer()
        self.timer.timeout.connect(self.emit_config)
        self.timer.start(50) 
        
    def emit_config(self):
        config = {
            'deadzone': self.deadzone.value() / 100.0, 
            'anti_deadzone': self.anti_deadzone.value() / 100.0,
            'k_low': self.k_low.value(),
            'k_high': self.k_high.value(),
            'smoothing': self.smoothing.value() / 100.0
        }
        self.signals.config_changed.emit(config)
        
    def update_visuals(self, lx, ly, rx, ry):
        self.l_display.update_pos(lx, ly)
        self.r_display.update_pos(rx, ry)
        self.l_label.setText(f"Left: ({lx:+.2f}, {ly:+.2f})")
        self.r_label.setText(f"Right: ({rx:+.2f}, {ry:+.2f})")

    def update_hidhide_status(self, installed, cloaking_active, whitelisted):
        if not installed:
            self.hh_status.setText("Status: Not Installed")
            self.hh_group.setEnabled(False)
            return
        
        status_text = "Status: Installed"
        if whitelisted:
            status_text += " | Whitelisted"
        else:
            status_text += " | NOT Whitelisted"
            
        self.hh_status.setText(status_text)
        self.cloak_cb.setChecked(cloaking_active)

def run_gui():
    app = QApplication(sys.argv)
    window = RCFilterGUI()
    window.show()
    return app, window

if __name__ == "__main__":
    app, win = run_gui()
    sys.exit(app.exec())
