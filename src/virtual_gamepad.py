import vgamepad as vg

class VirtualGamepad:
    def __init__(self):
        try:
            self.gamepad = vg.VX360Gamepad()
            print("Virtual Xbox 360 Gamepad initialized via ViGEmBus.")
        except Exception as e:
            print(f"CRITICAL: Failed to initialize virtual gamepad: {e}")
            print("Ensure ViGEmBus is installed on your system.")
            self.gamepad = None

    def map_float_to_int(self, value):
        # Maps [-1.0, 1.0] to [-32768, 32767]
        clamped = max(-1.0, min(1.0, value))
        if clamped >= 0:
            return int(clamped * 32767)
        else:
            return int(clamped * 32768)

    def update_sticks(self, lx, ly, rx, ry):
        if not self.gamepad:
            return
            
        lx_int = self.map_float_to_int(lx)
        ly_int = self.map_float_to_int(ly)
        rx_int = self.map_float_to_int(rx)
        ry_int = self.map_float_to_int(ry)
        
        self.gamepad.left_joystick(x_value=lx_int, y_value=ly_int)
        self.gamepad.right_joystick(x_value=rx_int, y_value=ry_int)
        
    def _set_btn(self, btn, pressed):
        if pressed:
            self.gamepad.press_button(button=btn)
        else:
            self.gamepad.release_button(button=btn)

    def update_controller(self, buttons_raw, l2_val, r2_val):
        """
        Maps DualSense buttons and analog triggers to Xbox 360.
        """
        if not self.gamepad or buttons_raw is None:
            return
            
        b1 = buttons_raw[0]
        b2 = buttons_raw[1]
        b3 = buttons_raw[2] # PS button byte
        
        # 1. Triggers (Analog)
        self.gamepad.left_trigger(value=l2_val)
        self.gamepad.right_trigger(value=r2_val)
        
        # 2. Face Buttons
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_X, bool(b1 & 16))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, bool(b1 & 32))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_B, bool(b1 & 64))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y, bool(b1 & 128))
        
        # 3. D-Pad
        dpad = b1 & 0x0F
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, dpad in (0, 1, 7))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, dpad in (3, 4, 5))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, dpad in (1, 2, 3))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, dpad in (5, 6, 7))

        # 4. Shoulders and Center Buttons
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, bool(b2 & 1))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, bool(b2 & 2))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK, bool(b2 & 16))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_START, bool(b2 & 32))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB, bool(b2 & 64))
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, bool(b2 & 128))
        
        # 5. Guide (PS) Button - DISABLED TO PREVENT SYSTEM INTERFERENCE
        self._set_btn(vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, False)
        
    def apply(self):
        if self.gamepad:
            self.gamepad.update()
            
if __name__ == "__main__":
    import time
    pad = VirtualGamepad()
    if pad.gamepad:
        print("Testing virtual controller with dummy data (2 seconds)...")
        pad.update_sticks(0.5, 0.5, -0.5, -0.5)
        pad.apply()
        time.sleep(2)
        pad.update_sticks(0.0, 0.0, 0.0, 0.0)
        pad.apply()
        print("Test finished.")
