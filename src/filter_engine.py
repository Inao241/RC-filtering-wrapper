import math

class FilterEngine:
    def __init__(self, deadzone=0.0, anti_deadzone=0.0, k_low=2.0, k_high=0.0, smoothing=0.7):
        self.deadzone = deadzone
        self.anti_deadzone = anti_deadzone
        self.k_low = k_low
        self.k_high = k_high
        self.smoothing = smoothing # 0.0 to 1.0 (Higher = more smoothing)
        
        self.prev_x = 0.0
        self.prev_y = 0.0
        self.raw_prev_x = 0.0
        self.raw_prev_y = 0.0

    def apply_smoothing(self, current, prev):
        # Simple EMA (Exponential Moving Average)
        return prev + (1.0 - self.smoothing) * (current - prev)

    def calculate_k(self, value):
        abs_val = abs(value)
        # If very close to center, reduce k to prevent jitter
        if abs_val < 0.02:
            return 0.0
            
        if abs_val < 0.3:
            return self.k_low
        elif abs_val > 0.8:
            return self.k_high
        else:
            return self.k_low + (self.k_high - self.k_low) * (abs_val - 0.3) / 0.5

    def apply_deadzone(self, value):
        if abs(value) < self.deadzone:
            return 0.0
        
        sign = 1.0 if value > 0 else -1.0
        # Safe division
        denom = 1.0 - self.deadzone
        if denom <= 0: return 0.0
        
        rescaled = (abs(value) - self.deadzone) / denom
        
        if self.anti_deadzone > 0:
            rescaled = self.anti_deadzone + rescaled * (1.0 - self.anti_deadzone)
            
        return sign * rescaled

    def process_axis(self, value, prev_filtered, raw_prev):
        # 1. First apply light smoothing to the raw input to kill high-frequency noise
        smooth_val = self.apply_smoothing(value, raw_prev)
        
        # 2. Apply deadzone logic
        deadzoned_val = self.apply_deadzone(smooth_val)
        
        # 3. Calculate dynamic k
        k = self.calculate_k(deadzoned_val)
        
        # 4. Derivative compensation (Negative RC)
        # Use the smoothed values for velocity calculation to prevent jitter amplification
        velocity = deadzoned_val - prev_filtered
        output = deadzoned_val + k * velocity
        
        # 5. Clamp
        return max(-1.0, min(1.0, output)), smooth_val, deadzoned_val

    def process(self, x, y):
        out_x, smooth_x, d_x = self.process_axis(x, self.prev_x, self.raw_prev_x)
        out_y, smooth_y, d_y = self.process_axis(y, self.prev_y, self.raw_prev_y)
        
        self.raw_prev_x = smooth_x
        self.raw_prev_y = smooth_y
        self.prev_x = d_x
        self.prev_y = d_y
        
        return out_x, out_y
