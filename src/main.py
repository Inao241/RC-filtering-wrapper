import time
import sys
import os
import threading
from PySide6.QtCore import QTimer

# Add src to path for imports
sys.path.append(os.path.dirname(__file__))

import vgamepad as vg
from pydualsense import pydualsense, DSState
from filter_engine import FilterEngine
from virtual_gamepad import VirtualGamepad
from gui import run_gui
from hidhide_manager import HidHideManager

class FilterWrapper:
    def __init__(self):
        # 0. Initialize HidHide (Auto-hiding and Whitelisting)
        self.hidhide = HidHideManager()
        if self.hidhide.is_installed():
            print("HidHide detected. Auto-configuring for exclusive access...")
            self.hidhide.setup_whitelisting()
            self.hidhide.hide_dualsense_edge()
        else:
            print("WARNING: HidHide not found. You may experience 'double input' in some games.")

        # 1. Initialize pydualsense
        self.ds = pydualsense()
        
        # 2. RC Filter Engines
        self.left_filter = FilterEngine(deadzone=0.0)
        self.right_filter = FilterEngine(deadzone=0.0)
        
        # 3. Virtual Xbox Gamepad
        self.vgamepad = VirtualGamepad()
        
        self.running = True
        self.monitor_mode = not self.vgamepad.gamepad
        
        # Shared state for GUI
        self.current_sticks = (0.0, 0.0, 0.0, 0.0)
        self.config_lock = threading.Lock()
        
        # Mapping table: pydualsense attributes -> vgamepad buttons
        self.button_map = {
            'cross': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            'circle': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            'square': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            'triangle': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            'L1': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            'R1': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            'share': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            'options': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
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
        print("Initializing DualSense Edge via pydualsense...")
        try:
            # Initialize connection
            while self.running:
                try:
                    self.ds.init()
                    print("DualSense Edge Connected!")
                    break
                except Exception as e:
                    print(f"Waiting for controller... ({e})")
                    time.sleep(2.0)
            
            # Main Processing Loop
            loop_count = 0
            while self.running and self.ds.device:
                # 1. Read Raw Sticks (-128 to 127 -> -1.0 to 1.0)
                state = self.ds.state
                
                # Center is around 128 unsigned or 0 signed. pydualsense handles signed.
                lx_norm = state.LX / 128.0
                ly_norm = state.LY / 128.0
                rx_norm = state.RX / 128.0
                ry_norm = state.RY / 128.0
                
                # 2. Apply RC Filtering
                with self.config_lock:
                    # Invert Y (In pydualsense, Y+ is Down, VGamepad Y+ is Up)
                    plx, ply = self.left_filter.process(lx_norm, -ly_norm)
                    prx, pry = self.right_filter.process(rx_norm, -ry_norm)
                
                self.current_sticks = (plx, ply, prx, pry)
                
                # Debug output every 500ms approx
                loop_count += 1
                if loop_count % 250 == 0:
                    print(f"Debug [Loop {loop_count}]: Raw_LX={state.LX:4d} Filtered_LX={plx:+.2f} | L2={state.L2_value:3d}")

                # 3. Output to Virtual Gamepad
                if not self.monitor_mode:
                    # Sticks
                    self.vgamepad.update_sticks(plx, ply, prx, pry)
                    
                    # Triggers (Ensure values are within 0-255)
                    self.vgamepad.gamepad.left_trigger(value=int(state.L2_value))
                    self.vgamepad.gamepad.right_trigger(value=int(state.R2_value))
                    
                    # Buttons
                    for ds_attr, xbox_btn in self.button_map.items():
                        val = getattr(state, ds_attr, False)
                        if val:
                            self.vgamepad.gamepad.press_button(button=xbox_btn)
                        else:
                            self.vgamepad.gamepad.release_button(button=xbox_btn)
                    
                    # D-Pad
                    if state.DpadUp: self.vgamepad.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                    else: self.vgamepad.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                    
                    if state.DpadDown: self.vgamepad.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                    else: self.vgamepad.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                    
                    if state.DpadLeft: self.vgamepad.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                    else: self.vgamepad.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                    
                    if state.DpadRight: self.vgamepad.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
                    else: self.vgamepad.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
                    
                    # Apply all changes
                    self.vgamepad.apply()
                
                # Stable frequency (1000Hz / 1ms)
                time.sleep(0.001)
                
        except Exception as e:
            print(f"Error in processing thread: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.ds.close()
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
            
            # Periodically update HidHide status (every 2 seconds or so)
            if hasattr(update_viz, "hh_counter"):
                update_viz.hh_counter += 1
            else:
                update_viz.hh_counter = 0
            
            if update_viz.hh_counter % 120 == 0: # Approx 2 seconds at 60fps
                window.update_hidhide_status(
                    wrapper.hidhide.is_installed(),
                    wrapper.hidhide.get_cloak_state(),
                    wrapper.hidhide.is_whitelisted()
                )
        
        # Connect HidHide signals
        window.signals.hidhide_toggle_cloak.connect(wrapper.hidhide.set_cloak)
        window.signals.hidhide_whitelist_self.connect(wrapper.hidhide.setup_whitelisting)
        window.signals.hidhide_auto_setup.connect(wrapper.hidhide.hide_dualsense_edge)

        timer = QTimer()
        timer.timeout.connect(update_viz)
        timer.start(16) # 60 FPS visual update
        
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
        print("Restoring controller visibility (Disabling HidHide)...")
        wrapper.hidhide.disable_hiding()
        
    sys.exit(code)

if __name__ == "__main__":
    main()
