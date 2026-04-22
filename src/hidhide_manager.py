import subprocess
import os
import sys
import json

class HidHideManager:
    def __init__(self):
        # Default paths for HidHide CLI
        paths = [
            r"C:\Program Files\Nefarius Software Solutions\HidHide\x64\HidHideCLI.exe",
            r"C:\Program Files\Nefarius Software Solutions\HidHide\bin\HidHideCLI.exe",
            r"C:\Program Files\Nefarius Software Labs\HidHide\bin\HidHideCLI.exe",
            r"C:\Program Files\Nefarius Software Labs\HidHide\x64\HidHideCLI.exe",
            r"C:\Program Files\Nefarius Software Solutions e.U\HidHide\HidHideCLI.exe",
            r"C:\Program Files\Nefarius Software Solutions e.U\HidHide\bin\HidHideCLI.exe"
        ]
        self.cli_path = None
        for p in paths:
            if os.path.exists(p):
                self.cli_path = p
                break

    def is_installed(self):
        return self.cli_path is not None

    def _run_cmd(self, args):
        if not self.is_installed():
            return None
        try:
            cmd = [self.cli_path] + args
            creationflags = 0x08000000 # CREATE_NO_WINDOW
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, creationflags=creationflags)
            return result.stdout.strip()
        except Exception as e:
            return None

    def get_cloak_state(self):
        """Returns True if cloaking is ON, False if OFF."""
        output = self._run_cmd(["--cloak-state"])
        if output:
            up = output.upper()
            return "ON" in up or "ENABLE" in up or "TRUE" in up
        return False

    def set_cloak(self, state: bool):
        arg = "--cloak-on" if state else "--cloak-off"
        return self._run_cmd([arg]) is not None

    def get_whitelist(self):
        output = self._run_cmd(["--app-list"])
        if output:
            return output.splitlines()
        return []

    def is_whitelisted(self, path=None):
        if path is None:
            path = sys.executable
        whitelist = self.get_whitelist()
        return any(path.lower() == item.lower() for item in whitelist)

    def setup_whitelisting(self):
        """Adds current python executable to HidHide whitelist."""
        py_exe = sys.executable
        if not self.is_whitelisted(py_exe):
            self._run_cmd(["--app-reg", py_exe])
            return True
        return False

    def get_devices(self, gaming_only=True):
        arg = "--dev-gaming" if gaming_only else "--dev-all"
        output = self._run_cmd([arg])
        if not output:
            return []
            
        # Try to parse as JSON first
        try:
            data = json.loads(output)
            device_paths = []
            for group in data:
                for dev in group.get('devices', []):
                    if dev.get('deviceInstancePath'):
                        device_paths.append(dev['deviceInstancePath'])
            return device_paths
        except:
            # Fallback to line-based parsing
            return output.splitlines()

    def hide_dualsense_edge(self):
        """
        Attempts to find DualSense Edge (VID: 054C, PID: 0DF2 or 0CE6) 
        and add it to the hidden list.
        """
        output = self._run_cmd(["--dev-gaming"])
        if not output:
            return False

        target_ids = ["054C:0DF2", "054C:0CE6"]
        found_paths = []

        try:
            data = json.loads(output)
            for group in data:
                for dev in group.get('devices', []):
                    instance_path = dev.get('deviceInstancePath')
                    if instance_path:
                        for target in target_ids:
                            if target.lower() in instance_path.lower():
                                found_paths.append(instance_path)
        except:
            # Fallback to line-based
            devices = output.splitlines()
            for dev in devices:
                for target in target_ids:
                    if target.lower() in dev.lower():
                        instance_path = dev.split()[0]
                        found_paths.append(instance_path)
        
        if not found_paths:
            return False
            
        for path in found_paths:
            self._run_cmd(["--dev-hide", path])
        
        self.set_cloak(True)
        return True

    def disable_hiding(self):
        """Disable the global cloak (unhide everything)."""
        return self.set_cloak(False)

if __name__ == "__main__":
    mgr = HidHideManager()
    if mgr.is_installed():
        print(f"HidHide CLI: {mgr.cli_path}")
        print(f"Cloak State: {mgr.get_cloak_state()}")
        # print(f"Devices: {mgr.get_devices()}")
    else:
        print("HidHide not found.")
