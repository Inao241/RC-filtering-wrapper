import hid

class DSE_HID_Reader:
    def __init__(self):
        self.vendor_id = 0x054C
        self.product_id_edge = 0x0DF2
        self.product_id_ds = 0x0CE6
        self.device = None

    def connect(self):
        # Enumerate and find the device
        devices = hid.enumerate(self.vendor_id)
        if not devices:
            return False
            
        for device_dict in devices:
            if device_dict['product_id'] in (self.product_id_edge, self.product_id_ds):
                try:
                    self.device = hid.device()
                    self.device.open(self.vendor_id, device_dict['product_id'])
                    self.device.set_nonblocking(True)
                    print(f"Connected: {device_dict.get('product_string', 'Unknown Device')} (PID: {hex(device_dict['product_id'])})")
                    return True
                except Exception as e:
                    print(f"Error opening HID device: {e}")
        return False

    def read_report(self):
        if not self.device:
            return None
        
        try:
            report = self.device.read(64)
            return report if report else None
        except OSError:
            print("Controller disconnected.")
            self.close()
            return None

    def parse_report(self, report):
        """
        Corrected offsets for DualSense Edge (USB):
        Stick Axes: 1, 2, 3, 4
        Analog Triggers: 5, 6
        Buttons: 7, 8, 9
        """
        if not report or len(report) < 10:
            return 0.0, 0.0, 0.0, 0.0, [8, 0, 0], 0, 0
            
        offset = 1
        if report[0] == 0x31: # Bluetooth has different mapping
            offset = 2
            
        lx_raw = report[offset]
        ly_raw = report[offset + 1]
        rx_raw = report[offset + 2]
        ry_raw = report[offset + 3]
        
        # Analog Triggers are BEFORE buttons on Edge
        l2_analog = report[offset + 4]
        r2_analog = report[offset + 5]
        
        # Buttons start at byte 7
        buttons = report[offset + 6 : offset + 9] 
        
        lx = (lx_raw / 127.5) - 1.0
        ly = (ly_raw / 127.5) - 1.0
        rx = (rx_raw / 127.5) - 1.0
        ry = (ry_raw / 127.5) - 1.0
        
        return lx, -ly, rx, -ry, buttons, l2_analog, r2_analog
        
    def close(self):
        if self.device:
            self.device.close()
            self.device = None
