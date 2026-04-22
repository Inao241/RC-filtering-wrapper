from pydualsense import pydualsense
import time

ds = pydualsense()
try:
    ds.init()
    print("DualSense Edge Connected. Reading raw values for 2 seconds...")
    start = time.time()
    while time.time() - start < 2:
        state = ds.state
        print(f"\rRaw Sticks: LX={state.LX}, LY={state.LY} | Triggers: L2={state.L2}, R2={state.R2}", end="")
        time.sleep(0.1)
    print("\nTest finished.")
finally:
    ds.close()
