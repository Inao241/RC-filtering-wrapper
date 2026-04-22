# Universal RC Filter Tuner

A professional input wrapper and signal processing tool for game controllers. This tool applies a **Negative RC Filter** and custom response curves to your controller sticks to eliminate input lag and provide a more responsive gaming experience.

## Features

*   **Universal Controller Support**:
    *   **DualSense / DualSense Edge**: High-precision support via `pydualsense`.
    *   **DualShock 4**: Native HID support for low latency.
    *   **Xbox Series/One/360**: Supported via XInput/Pygame.
    *   **Generic Controllers**: Supports any controller recognized by Windows.
*   **Negative RC Filter**: A forward-prediction algorithm that compensates for physical sensor lag.
*   **Real-time GUI**: Tuner interface built with PySide6 for live monitoring and adjustment.
*   **HidHide Integration**: One-click setup to prevent "double input" by hiding the physical controller from games while keeping the virtual one visible.
*   **Virtual Xbox 360 Emulation**: Forwards processed inputs to a virtual controller compatible with all modern games.

## Installation

1.  **Drivers Required**:
    *   [ViGEmBus](https://github.com/ViGEm/ViGEmBus/releases): Required for virtual controller emulation.
    *   [HidHide](https://github.com/ViGEm/HidHide/releases) (Optional): Recommended to prevent double-input issues.
2.  **Download**: Run the `RC_Filter.exe` from the `dist` folder.

## Usage

1.  Connect your controller.
2.  Run `RC_Filter.exe` as Administrator (required for HidHide and virtual device management).
3.  Adjust the filter parameters:
    *   **Deadzone**: Standard inner deadzone.
    *   **Anti-Deadzone**: Removes built-in controller/game deadzones.
    *   **K Low/High**: Adjusts the intensity of the RC filter (prediction).
    *   **Smoothing**: Reduces high-frequency noise.
4.  (Optional) Use the **HidHide** section to "Auto-Hide Controllers" for a seamless exclusive mode.

## Technical Details

The **Negative RC Filter** uses the formula:
`Output = Input + k * (Input - Previous_Input)`
This compensates for the delay in physical stick movement by predicting the target position based on velocity.

## License
MIT
