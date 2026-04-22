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
            
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Generic Controller Initialized: {self.joystick.get_name()}")
            return True
        return False
        
    def read(self):
        if not self.joystick: return False
        pygame.event.pump()
        
        # Note: Axis mapping varies, this is standard Xbox layout for Pygame
        self.state.LX = self.joystick.get_axis(0)
        self.state.LY = self.joystick.get_axis(1)
        self.state.RX = self.joystick.get_axis(2)
        self.state.RY = self.joystick.get_axis(3)
        
        # Triggers: In many mappings, L2 is axis 4, R2 is axis 5 (range -1 to 1)
        # We'll try to detect common mappings
        if self.joystick.get_numaxes() >= 6:
            l2_raw = self.joystick.get_axis(4)
            r2_raw = self.joystick.get_axis(5)
            # Normalize from [-1, 1] to [0, 1]
            self.state.L2 = (l2_raw + 1.0) / 2.0
            self.state.R2 = (r2_raw + 1.0) / 2.0
        
        # Buttons
        num_buttons = self.joystick.get_numbuttons()
        # Common Xbox Mapping: 0:A, 1:B, 2:X, 3:Y, 4:Back, 6:Start, 7:L3, 8:R3, 9:LB, 10:RB
        btn_map = {
            'A': 0, 'B': 1, 'X': 2, 'Y': 3,
            'L1': 4, 'R1': 5,
            'Back': 6, 'Start': 7,
            'L3': 8, 'R3': 9,
            'Guide': 10
        }
        for name, idx in btn_map.items():
            if idx < num_buttons:
                self.state.buttons[name] = self.joystick.get_button(idx)
        
        # D-Pad (Hat)
        if self.joystick.get_numhats() > 0:
            self.state.dpad = self.joystick.get_hat(0)
            
        return True
        
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
