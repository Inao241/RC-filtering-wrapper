

# System Design Document: DualSense Edge (DSE) Input Wrapper & Custom Filter Engine

## 1. Project Overview
**Objective:** Develop a Python-based input wrapper for the PlayStation DualSense Edge (DSE) controller. The software will intercept raw HID reports from the DSE, apply custom signal processing algorithms (specifically a Negative RC Filter and custom response curves) to the analog sticks, and emulate a virtual controller (Xbox 360) to forward the processed inputs to the OS/games.
**Target Environment:** Windows 11/10
**Primary Language:** Python 3.10+
**Core Dependencies:** * `hid` (for reading raw USB/Bluetooth HID reports)
* `vgamepad` (for ViGEmBus virtual controller emulation)

## 2. System Architecture & Modules

The system should be strictly modularized into Object-Oriented classes to allow for easy algorithm swapping and GitHub repository management. 

### Module 1: `DSE_HID_Reader`
* **Responsibility:** Interface with the physical DSE controller.
* **Hardware IDs:** Connect via Vendor ID (`0x054C`) and Product ID (`0x0DF2` for Edge, optionally fallback to `0x0CE6` for standard DualSense).
* **Output:** Parse the raw byte array to extract normalized Right Stick (RX, RY) and Left Stick (LX, LY) values in the float range `[-1.0, 1.0]`. 
* *Note for AI:* Implement a non-blocking read loop. DSE standard HID report format places stick data at specific byte offsets (typically bytes 1-4 for standard reports, or offset by 1 in Bluetooth).

### Module 2: `FilterEngine`
* **Responsibility:** Apply mathematical transformations to the normalized raw stick inputs.
* **Component A: Anti-Deadzone / Deadzone Handler**
    * Implement standard inner/outer deadzone logic.
* **Component B: Negative RC Filter (Derivative Compensation)**
    * **Goal:** Eliminate physical sensor input lag by applying forward-prediction based on stick velocity.
    * **Formula:** $Output_t = x_t + k \cdot (x_t - x_{t-1})$ 
    * *Where:* $x_t$ is current input, $x_{t-1}$ is previous frame input, $k$ is the compensation intensity factor (e.g., `0.5` to `2.0`).
    * Must include clamping to ensure the final output remains strictly within `[-1.0, 1.0]`.
    * Support dynamic $k$ mapping (e.g., high $k$ when $|x_t| < 0.3$, $k=0$ when $|x_t| > 0.8$).

### Module 3: `Virtual_Gamepad`
* **Responsibility:** Take the processed floating-point values from `FilterEngine` and convert them back into the format required by `vgamepad`.
* **Action:** Instantiate a `vgamepad.VX360Gamepad()`. Map the processed `[-1.0, 1.0]` floats to the XInput integer range `[-32768, 32767]`.
* **Pass-through:** Map all standard face buttons, bumpers, and triggers directly from the `DSE_HID_Reader` to the virtual gamepad without algorithmic alteration.

### Module 4: `Main_Loop`
* **Responsibility:** Orchestrate the data flow at a high polling rate.
* **Performance Requirement:** The loop must execute as fast as possible to match or exceed the 250Hz/1000Hz polling rate of the controller. Avoid heavy print statements or blocking I/O in this loop.
* **Logic Flow:**
    1. Wait for / read new HID report.
    2. Extract Stick X/Y.
    3. Pass through `FilterEngine.process()`.
    4. Update `Virtual_Gamepad` state.
    5. Call `Virtual_Gamepad.update()`.

## 3. Initial Tasks for the AI Assistant

Please generate the initial codebase following this sequence:
1.  **Task 1:** Write the `FilterEngine` class implementing the Negative RC Filter math and state management. Include simple unit tests to verify the math logic.
2.  **Task 2:** Write the `Virtual_Gamepad` class using `vgamepad` with dummy data input to verify the virtual controller spawns correctly in Windows.
3.  **Task 3:** Write the `DSE_HID_Reader` and the `Main_Loop`. *Ensure you handle the HID device enumeration and gracefully catch disconnection exceptions.*

