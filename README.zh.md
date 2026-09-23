# Claw CrossFire AIR：系统托盘控制

🇹🇷 [Türkçe](README.tr.md) · 🇬🇧 [English](README.md) · 🇪🇸 [Español](README.es.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇷🇺 [Русский](README.ru.md) · 🇨🇳 **中文** · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇸🇦 [العربية](README.ar.md)

一个用于 **Claw CrossFire AIR V1** 无线鼠标的小型系统托盘程序。不需要厂商软件，也不需要其 DLL：它通过 USB HID 直接与鼠标通信。支持 Windows，Linux 支持处于测试阶段。

![托盘菜单](docs/screenshot.png)

## 功能

| | |
|---|---|
| **电池** | 托盘中以大数字显示电量百分比，充电时显示黄色边框。开始和结束充电、充满、电量到 20% 和 10% 时发出通知。鼠标休眠时图标显示 `II`，鼠标未连接时图标隐藏。 |
| **右键菜单包含全部设置** | DPI 档位（数值、当前档位、档位数量）、回报率、去抖动、运动同步、直线修正、波纹控制、最高性能、灯光模式、颜色、亮度、速度、移动时关灯、关灯延时、DPI 指示灯、远距离模式。每次写入都会从鼠标回读并校验。 |
| **五个可编辑预设** | 游戏、桌面、精确、省电、演示。一键应用，把鼠标当前设置保存到预设，重命名，恢复默认。保存在 `config.json` 中。 |
| **帮助** | 帮助子菜单列出每个设置；点击后以通知形式显示简短说明。"打开指南"在可滚动窗口中显示全部说明。 |
| **十种语言** | Türkçe、English、Español、Français、Deutsch、Русский、中文、日本語、한국어、العربية。跟随系统语言，也可在菜单中切换；选择会被记住。 |
| **轻量** | 只有一个托盘图标，无服务、无驱动，除 `config.json` 外不在自身文件夹之外写入任何内容。可随 Windows 启动。 |

> 本程序与厂商无关。协议通过观察厂商软件逆向得到，仅在 **CrossFire AIR V1**（PixArt PAW3325，固件 v2.0，2.4 GHz 接收器）上测试过。使用风险自负。

## 安装

### 方式 A：现成的可执行文件（无需 Python）

1. 从 [Releases](https://github.com/Yerlifan/claw-crossfire-air-tray/releases) 页面下载 `ClawTray_<版本>_win64.zip`，解压到任意文件夹。
2. 运行 `ClawTray.exe`。图标出现在托盘中（可能在 `^` 溢出区域内）。
3. 可选，创建开始菜单、桌面和开机启动快捷方式：
   ```powershell
   powershell -ExecutionPolicy Bypass -File kurulum.ps1
   ```

首次运行时 Windows SmartScreen 可能因程序未签名而警告；选择"更多信息，仍要运行"，或使用方式 B。

### 方式 B：从源代码运行

要求：Windows 10/11（或 Linux，见方式 C），Python 3.10 或更高版本。

```powershell
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
pip install -r requirements.txt
pythonw claw_tray.py
```

卸载：运行 `kurulum.ps1 -Kaldir` 后删除文件夹。命令行：`--status` 显示当前状态，`--lang zh` 强制语言，`--guide` 打开指南。

### 方式 C：Linux（测试版，尚未在真实硬件上测试）

鼠标本身在 Linux 上无需驱动；本程序只是增加托盘中的电池和设置界面。Linux 移植只在未连接鼠标的虚拟机中验证过，欢迎来自真实硬件的反馈。

```bash
./linux/kurulum.sh        # udev 规则（sudo）、pip 包、.desktop + 自启动
```

Debian/Ubuntu 软件包：`sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 python3-tk`；GNOME 还需启用 *AppIndicator* 扩展。卸载：`./linux/kurulum.sh -u`。

## 注意事项

- **不能与 CrossFire 软件同时运行。** 两者同时与鼠标通信时 CrossFire 会崩溃（鼠标不受影响），因此 CrossFire 运行期间本程序会自动暂停（图标显示 `!`）。可以卸载 CrossFire，本程序不依赖它。
- 鼠标休眠时（约一分钟无操作）无法写入设置：图标显示 `II`，移动鼠标后自动恢复。
- 如果出现问题，厂商软件中的 *Restore* 可将鼠标恢复出厂设置。
- 宏和按键重映射有意不在范围内。

## 协议细节

数据包格式、命令表和设置存储映射见[英文 README](README.md#how-it-works)。`claw_proto.py` 是完整的协议层，可单独使用。

## 许可证

MIT，见 [LICENSE](LICENSE)。
