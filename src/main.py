import os
import sys
import threading
import time
import importlib.util

# DLL resolution fix for Python 3.8+ on Windows
if os.name == 'nt' and hasattr(os, 'add_dll_directory'):
    spec = importlib.util.find_spec('pydualsense')
    if spec and spec.origin:
        ds_dir = os.path.dirname(spec.origin)
        if os.path.isdir(ds_dir):
            os.add_dll_directory(ds_dir)

from PySide6.QtCore import QTimer

# Add src to path for imports
sys.path.append(os.path.dirname(__file__))

import vgamepad as vg
from filter_engine import FilterEngine
from virtual_gamepad import VirtualGamepad
from gui import run_gui
from hidhide_manager import HidHideManager
from controllers import ControllerFactory

class FilterWrapper:
    def __init__(self):
        # 0. Initialize HidHide
        self.hidhide = HidHideManager()
        if self.hidhide.is_installed():
            print("HidHide detected. Auto-configuring for exclusive access...")
            # CRITICAL: Whitelist the python executable BEFORE hiding anything
            self.hidhide.setup_whitelisting()
            self.hidhide.hide_controllers()
            print("HidHide: Python whitelisted and controllers hidden.")
        else:
            print("WARNING: HidHide not found. You may experience 'double input' in some games.")

        # 1. Initialize Controller
        self.controller = None
        
        # 2. RC Filter Engines
        self.left_filter = FilterEngine(deadzone=0.0)
        self.right_filter = FilterEngine(deadzone=0.0)
        
        # 3. Virtual Xbox Gamepad Placeholder
        self.vgamepad = None
        
        self.running = True
        self.monitor_mode = True
        
        # Shared state for GUI
        self.current_sticks = (0.0, 0.0, 0.0, 0.0)
        self.config_lock = threading.Lock()
        
        # Unified mapping table: ControllerState names -> vgamepad buttons
        self.button_map = {
            'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            'X': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            'Y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            'L1': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            'R1': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            'Back': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            'Start': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            'L3': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            'R3': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
        }

    def update_config(self, config):
        with self.config_lock:
            for f in [self.left_filter, self.right_filter]:
                f.deadzone = config['deadzone']
                f.anti_deadzone = config['anti_deadzone']
                f.k_low = config['k_low']
                f.k_high = config['k_high']
                f.smoothing = config.get('smoothing', 0.5)

    def run_loop(self):
        print("Searching for controller...")
        try:
            # Initialize connection
            while self.running:
                self.controller = ControllerFactory.get_controller()
                if self.controller:
                    print(f"Controller Connected!")
                    break
                time.sleep(1.0)
            
            # 3. Virtual Xbox Gamepad - Initialize AFTER we find the physical one
            # to avoid picking up ourselves in Pygame
            self.vgamepad = VirtualGamepad()
            self.monitor_mode = not self.vgamepad.gamepad
            
            # Main Processing Loop
            while self.running and self.controller:
                # 1. Read Raw State
                if not self.controller.read():
                    print("Controller read failed, reconnecting...")
                    self.controller = None
                    while self.running and not self.controller:
                        self.controller = ControllerFactory.get_controller()
                        time.sleep(1.0)
                    continue
                
                state = self.controller.state
                
                # 2. Apply RC Filtering
                with self.config_lock:
                    # Note: Pygame sticks use Y- as Up. Our filter usually wants Y+ as Up.
                    # Standard Xbox/Generic: Up is -1.0, Down is 1.0. 
                    # We negate state.LY/RY to get Up as +1.0.
                    plx, ply = self.left_filter.process(state.LX, -state.LY)
                    prx, pry = self.right_filter.process(state.RX, -state.RY)
                
                self.current_sticks = (plx, ply, prx, pry)
                
                # Debug output every 500ms if sticks are moving
                if abs(state.LX) > 0.1 or abs(state.LY) > 0.1:
                     # Using a simple counter for rate limiting
                     if not hasattr(self, "_dbg_tick"): self._dbg_tick = 0
                     self._dbg_tick += 1
                     if self._dbg_tick % 100 == 0:
                         print(f"RAW INPUT: LX={state.LX:.2f} LY={state.LY:.2f} | PROCESSED: {plx:.2f} {ply:.2f}")
                
                # 3. Output to Virtual Gamepad
                if not self.monitor_mode:
                    # Sticks
                    self.vgamepad.update_sticks(plx, ply, prx, pry)
                    
                    # Triggers (Ensure values are within 0-255)
                    self.vgamepad.gamepad.left_trigger(value=int(state.L2 * 255))
                    self.vgamepad.gamepad.right_trigger(value=int(state.R2 * 255))
                    
                    # Buttons
                    for btn_name, xbox_btn in self.button_map.items():
                        val = state.buttons.get(btn_name, False)
                        if val:
                            self.vgamepad.gamepad.press_button(button=xbox_btn)
                        else:
                            self.vgamepad.gamepad.release_button(button=xbox_btn)
                    
                    # D-Pad
                    dx, dy = state.dpad
                    if dy > 0: self.vgamepad.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                    else: self.vgamepad.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                    
                    if dy < 0: self.vgamepad.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                    else: self.vgamepad.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                    
                    if dx < 0: self.vgamepad.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                    else: self.vgamepad.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                    
                    if dx > 0: self.vgamepad.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
                    else: self.vgamepad.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
                    
                    # Apply all changes
                    self.vgamepad.apply()
                
                # Stable frequency
                time.sleep(0.001)
                
        except Exception as e:
            print(f"Error in processing thread: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.controller:
                self.controller.close()
            print("Processing thread stopped.")

def main():
    wrapper = FilterWrapper()
    
    # Start processing in a background thread
    proc_thread = threading.Thread(target=wrapper.run_loop, daemon=True)
    proc_thread.start()
    
    # Run GUI on main thread
    try:
        app, window = run_gui()
        
        # Connect GUI signals
        window.signals.config_changed.connect(wrapper.update_config)
        
        # Timer to update GUI visuals from wrapper state
        def update_viz():
            lx, ly, rx, ry = wrapper.current_sticks
            window.update_visuals(lx, ly, rx, ry)
            
            # Periodically update HidHide status
            if hasattr(update_viz, "hh_counter"):
                update_viz.hh_counter += 1
            else:
                update_viz.hh_counter = 0
            
            if update_viz.hh_counter % 120 == 0: 
                window.update_hidhide_status(
                    wrapper.hidhide.is_installed(),
                    wrapper.hidhide.get_cloak_state(),
                    wrapper.hidhide.is_whitelisted()
                )
        
        # Connect HidHide signals
        window.signals.hidhide_toggle_cloak.connect(wrapper.hidhide.set_cloak)
        window.signals.hidhide_whitelist_self.connect(wrapper.hidhide.setup_whitelisting)
        window.signals.hidhide_auto_setup.connect(wrapper.hidhide.hide_controllers)

        timer = QTimer()
        timer.timeout.connect(update_viz)
        timer.start(16) 
        
        print("GUI started. Close the window to stop.")
        code = app.exec()
    except Exception as gui_e:
        print(f"GUI failed to start: {gui_e}")
        print("Falling back to console-only mode. Press Ctrl+C to stop.")
        try:
            while wrapper.running:
                lx, ly, rx, ry = wrapper.current_sticks
                print(f"\rSticks: LX:{lx:+.2f} LY:{ly:+.2f} | RX:{rx:+.2f} RY:{ry:+.2f}", end="")
                time.sleep(0.05)
        except KeyboardInterrupt:
            pass
        code = 0
    wrapper.running = False
    proc_thread.join(timeout=1.0)
    
    # Restore HidHide state on exit
    if wrapper.hidhide.is_installed():
        print("Restoring controller visibility...")
        wrapper.hidhide.disable_hiding()
        
    sys.exit(code)

if __name__ == "__main__":
    main()
