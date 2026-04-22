from pydualsense import pydualsense
import time

ds = pydualsense()
try:
    ds.init()
    print("DualSense Edge Connected. PLEASE HOLD DOWN BOTH TRIGGERS NOW...")
    time.sleep(1.0) # Give user time to press
    
    state = ds.state
    print("\n--- All State Attributes ---")
    for attr in dir(state):
        if not attr.startswith('__') and not callable(getattr(state, attr)):
            val = getattr(state, attr)
            print(f"{attr}: {val} ({type(val).__name__})")
            
finally:
    ds.close()
