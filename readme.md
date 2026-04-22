# Universal RC Filter Tuner

A professional input wrapper and signal processing tool for game controllers. This tool applies a **Negative RC Filter** and custom response curves to your controller sticks to eliminate input lag and provide a more responsive gaming experience.

## 🚀 快速启动 (Windows)

1.  **驱动准备 (必选)**:
    *   安装 [ViGEmBus](https://github.com/ViGEm/ViGEmBus/releases): 虚拟手柄后端驱动。
    *   (推荐) 安装 [HidHide](https://github.com/ViGEm/HidHide/releases): 防止“双输入”问题的驱动。
2.  **启动程序**:
    *   直接双击根目录下的 **`run.bat`**。
    *   脚本会自动执行以下操作：
        *   检查并创建 Python 虚拟环境 (`venv`)。
        *   自动通过 `pip` 安装所有必要的依赖项。
        *   解决 Windows 下 `PySide6` 的 DLL 兼容性问题。
        *   启动 GUI 界面。

## ✨ 主要功能

*   **全手柄支持**: 
    *   **DualSense / DualSense Edge**: 支持触觉反馈和高精度读取。
    *   **DualShock 4**: 低延迟原生 HID 支持。
    *   **Xbox Series/One/360**: 完美的 XInput 兼容。
*   **Negative RC Filter**: 一种前馈预测算法，旨在补偿摇杆传感器的物理延迟。
*   **实时调试 GUI**: 基于 `PySide6` 构建，支持参数实时调节与监控。
*   **HidHide 一键集成**: 自动检测并配置 HidHide，防止物理手柄与虚拟手柄冲突。
*   **虚拟 Xbox 360 模拟**: 处理后的信号将映射至虚拟手柄，适配所有主流游戏。

## 🛠️ 参数说明

*   **Deadzone**: 标准内部死区。
*   **Anti-Deadzone**: 抵消游戏或手柄自带的硬件死区。
*   **K Low/High**: 调整 RC 滤波器（预测）的强度。
*   **Smoothing**: 减少高频噪声，平滑输入信号。

## ⚠️ 常见问题排查

*   **DLL load failed**: 如果你手动运行脚本报错 `QtCore: The specified procedure could not be found`，请确保使用我们提供的 `run.bat` 启动，或者参考 `requirements.txt` 使用 `PySide6==6.8.1` 以上版本。
*   **双重输入**: 请确保安装并启用了 HidHide。程序在启动时会自动尝试勾选 HidHide 的相关设置。

## 📄 开源协议
MIT License
