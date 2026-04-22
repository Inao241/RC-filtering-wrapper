import time
import hid
from pydualsense import pydualsense
import pygame

class ControllerState:
    def __init__(self):
        self.LX = 0.0
        self.LY = 0.0
        self.RX = 0.0
        self.RY = 0.0
        self.L2 = 0.0 # 0.0 to 1.0
        self.R2 = 0.0 # 0.0 to 1.0
        self.buttons = {} # Mapping of standard names to bool
        self.dpad = (0, 0) # (x, y) where -1, 0, 1

class BaseController:
    def __init__(self):
        self.state = ControllerState()
    
    def init(self):
        return False
        
    def read(self):
        """Update self.state and return True if successful."""
        return False
        
    def close(self):
        pass

class DualSenseController(BaseController):
    def __init__(self):
        super().__init__()
        self.ds = pydualsense()
        
    def init(self):
        try:
            self.ds.init()
            return True
        except:
            return False
            
    def read(self):
        if not self.ds.device:
            return False
        
        ds_state = self.ds.state
        self.state.LX = ds_state.LX / 128.0
        self.state.LY = ds_state.LY / 128.0
        self.state.RX = ds_state.RX / 128.0
        self.state.RY = ds_state.RY / 128.0
        self.state.L2 = ds_state.L2_value / 255.0
        self.state.R2 = ds_state.R2_value / 255.0
        
        self.state.buttons = {
            'A': ds_state.cross,
            'B': ds_state.circle,
            'X': ds_state.square,
            'Y': ds_state.triangle,
            'L1': ds_state.L1,
            'R1': ds_state.R1,
            'Back': ds_state.share,
            'Start': ds_state.options,
            'L3': ds_state.L3,
            'R3': ds_state.R3,
            'Guide': ds_state.ps
        }
        
        dx = 0
        if ds_state.DpadRight: dx = 1
        elif ds_state.DpadLeft: dx = -1
        
        dy = 0
        if ds_state.DpadUp: dy = 1
        elif ds_state.DpadDown: dy = -1
        
        self.state.dpad = (dx, dy)
        return True
        
    def close(self):
        self.ds.close()

class DualShock4Controller(BaseController):
    def __init__(self):
        super().__init__()
        self.vendor_id = 0x054C
        self.product_ids = [0x05C4, 0x09CC]
        self.device = None
        
    def init(self):
        devices = hid.enumerate(self.vendor_id)
        for d in devices:
            if d['product_id'] in self.product_ids:
                try:
                    self.device = hid.device()
                    self.device.open(self.vendor_id, d['product_id'])
                    self.device.set_nonblocking(True)
                    return True
                except:
                    continue
        return False
        
    def read(self):
        if not self.device: return False
        try:
            report = self.device.read(64)
            if not report: return True # No new data, keep old state
            
            # Basic DS4 USB Report Parsing
            # Offset 1-4: Sticks, 5: Buttons, 6: Buttons/DPad, 8: L2, 9: R2
            self.state.LX = (report[1] / 127.5) - 1.0
            self.state.LY = (report[2] / 127.5) - 1.0
            self.state.RX = (report[3] / 127.5) - 1.0
            self.state.RY = (report[4] / 127.5) - 1.0
            
            self.state.L2 = report[8] / 255.0
            self.state.R2 = report[9] / 255.0
            
            # Buttons (Byte 5)
            b5 = report[5]
            dpad_val = b5 & 0x0F
            self.state.buttons['X'] = bool(b5 & 16)
            self.state.buttons['A'] = bool(b5 & 32)
            self.state.buttons['B'] = bool(b5 & 64)
            self.state.buttons['Y'] = bool(b5 & 128)
            
            # DPad mapping (0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW, 8=Released)
            d_x, d_y = 0, 0
            if dpad_val in (7, 0, 1): d_y = 1
            if dpad_val in (3, 4, 5): d_y = -1
            if dpad_val in (1, 2, 3): d_x = 1
            if dpad_val in (5, 6, 7): d_x = -1
            self.state.dpad = (d_x, d_y)
            
            # Buttons (Byte 6)
            b6 = report[6]
            self.state.buttons['L1'] = bool(b6 & 1)
            self.state.buttons['R1'] = bool(b6 & 2)
            self.state.buttons['Back'] = bool(b6 & 16)
            self.state.buttons['Start'] = bool(b6 & 32)
            self.state.buttons['L3'] = bool(b6 & 64)
            self.state.buttons['R3'] = bool(b6 & 128)
            
            return True
        except:
            return False
            
    def close(self):
        if self.device:
            self.device.close()
            self.device = None

class GenericController(BaseController):
    """Uses Pygame for Xbox and other standard controllers."""
    def __init__(self):
        super().__init__()
        self.joystick = None
        
    def init(self):
        if not pygame.get_init():
            pygame.init()
        if not pygame.joystick.get_init():
            pygame.joystick.init()
            
        pygame.event.pump()
        count = pygame.joystick.get_count()
        if count > 0:
            print(f"Detected {count} joysticks.")
            
            # Find the best candidate:
            # If multiple controllers, prefer the one that ISN'T named exactly like a generic "Xbox 360 Controller" 
            # OR pick the one that is NOT index 0 if index 0 is suspicious.
            # Actually, most physical controllers have non-zero GUIDs.
            candidate = None
            for i in range(count):
                js = pygame.joystick.Joystick(i)
                js.init()
                name = js.get_name()
                guid = js.get_guid()
                print(f"Joystick {i}: {name} (GUID: {guid})")
                
                # Heuristic: Virtual Xbox 360 controllers from ViGEmBus often have 
                # a very specific GUID or generic name. 
                # If we have two Xbox controllers, the one with index 0 is usually the older one.
                # If we're starting fresh, index 0 is likely the physical one.
                # BUT if we restarted, index 0 might be the virtual one left over.
                
                # For now, let's take the one that is NOT the last one if count > 1?
                # Actually, a better way: Pick the one that has valid axis 4/5 (Triggers) 
                # initialized to -1.0 (typical for physical).
                if js.get_numaxes() >= 6:
                    t1 = js.get_axis(4)
                    if t1 < -0.9: # Physical Xbox triggers idle at -1.0
                        print(f"-> Selected {i} as physical candidate based on trigger idle state.")
                        candidate = js
                        break
                
                if not candidate:
                    candidate = js
            
            if candidate:
                self.joystick = candidate
                print(f"Final Selection: {self.joystick.get_name()}")
                return True
        return False
        
    def read(self):
        if not self.joystick: return False
        pygame.event.pump()
        
        try:
            # Axis mapping for Xbox 360/One controllers on Windows
            # 0:LX, 1:LY, 2:RX, 3:RY, 4:LT, 5:RT
            self.state.LX = self.joystick.get_axis(0)
            self.state.LY = self.joystick.get_axis(1)
            
            # Some older controllers or drivers map RX/RY differently
            num_axes = self.joystick.get_numaxes()
            if num_axes >= 4:
                self.state.RX = self.joystick.get_axis(2)
                self.state.RY = self.joystick.get_axis(3)
            
            # Triggers
            if num_axes >= 6:
                # LT/RT range is -1.0 (idle) to 1.0 (pressed)
                l2_raw = self.joystick.get_axis(4)
                r2_raw = self.joystick.get_axis(5)
                self.state.L2 = max(0.0, (l2_raw + 1.0) / 2.0)
                self.state.R2 = max(0.0, (r2_raw + 1.0) / 2.0)
            
            # Buttons
            num_buttons = self.joystick.get_numbuttons()
            # Standard Xbox: 0:A, 1:B, 2:X, 3:Y, 4:LB, 5:RB, 6:Back, 7:Start, 8:LS, 9:RS
            btn_map = {'A':0, 'B':1, 'X':2, 'Y':3, 'L1':4, 'R1':5, 'Back':6, 'Start':7, 'L3':8, 'R3':9}
            for name, idx in btn_map.items():
                if idx < num_buttons:
                    self.state.buttons[name] = bool(self.joystick.get_button(idx))
            
            # D-Pad
            if self.joystick.get_numhats() > 0:
                self.state.dpad = self.joystick.get_hat(0)
                
            return True
        except Exception as e:
            print(f"Read error: {e}")
            return False
        
    def close(self):
        if self.joystick:
            self.joystick.quit()

class ControllerFactory:
    @staticmethod
    def get_controller():
        # Order of preference: DualSense -> DualShock4 -> Generic (Xbox)
        
        # 1. Try DualSense
        ds = DualSenseController()
        if ds.init():
            return ds
            
        # 2. Try DS4
        ds4 = DualShock4Controller()
        if ds4.init():
            return ds4
            
        # 3. Try Generic
        gen = GenericController()
        if gen.init():
            return gen
            
        return None
