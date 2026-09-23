# Claw CrossFire AIR: tray control

🇹🇷 [Türkçe](README.tr.md) · 🇬🇧 **English** · 🇪🇸 [Español](README.es.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇷🇺 [Русский](README.ru.md) · 🇨🇳 [中文](README.zh.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇸🇦 [العربية](README.ar.md)

A small system tray app for the **Claw CrossFire AIR V1** wireless mouse. It needs neither the vendor's software nor its DLL: it talks to the mouse directly over USB HID. Windows, with Linux support in beta.

## Features

| | |
|---|---|
| **Battery** | Percentage as a big number in the tray, yellow frame while charging. Notifications when charging starts or stops, when the battery is full, and at 20% and 10%. The icon shows `II` while the mouse sleeps and hides when the mouse is not connected. |
| **Every setting in the right click menu** | DPI stages (values, active stage, number of stages), report rate, debounce, motion sync, angle snapping, ripple control, peak performance, lighting mode, colour, brightness, speed, lights off while moving, lights off delay, DPI indicator light, long range mode. Every write is read back from the mouse and verified. |
| **Five editable presets** | Gaming, Desktop, Precision, Battery Saver, Presentation. Apply with one click, save the mouse's current settings into a slot, rename a slot, reset it to default. Stored in `config.json`. |
| **Help** | A Help submenu lists every setting; clicking one shows a short explanation as a notification. "Open Guide" shows all explanations in a scrollable window. |
| **Ten languages** | Türkçe, English, Español, Français, Deutsch, Русский, 中文, 日本語, 한국어, العربية. Follows the system language and can be switched from the menu; the choice is remembered. |
| **Lightweight** | One tray icon, no service, no driver, nothing written outside its own folder except `config.json`. Starts with Windows if you want it to. |

> Not affiliated with the manufacturer. The protocol was reverse engineered by observing the vendor software and has been tested only on the **CrossFire AIR V1** (PixArt PAW3325, firmware v2.0, 2.4 GHz receiver). Use at your own risk.

## Install

### Option A: ready made executable (no Python needed)

1. Download `ClawTray_<version>_win64.zip` from the [Releases](https://github.com/Yerlifan/claw-crossfire-air-tray/releases) page and unzip it anywhere (e.g. `C:\Users\<you>\ClawTray`).
2. Run `ClawTray.exe`. The icon appears in the tray (possibly under the `^` overflow).
3. Optional, shortcuts in the Start menu, on the desktop and at Windows startup:
   ```powershell
   powershell -ExecutionPolicy Bypass -File kurulum.ps1
   ```

Windows SmartScreen may warn about an unsigned executable the first time; choose *More info, Run anyway*, or use option B.

### Option B: from source

Requirements: Windows 10/11 (or Linux, see option C), Python 3.10+.

```powershell
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
pip install -r requirements.txt
pythonw claw_tray.py
```

`kurulum.ps1` works here too (it uses `pythonw` when there is no `ClawTray.exe` next to it). To uninstall: `kurulum.ps1 -Kaldir`, then delete the folder.

Command line: `--status` prints the current state, `--lang en` forces a language, `--guide` opens the guide window.

### Option C: Linux (beta, not yet tested on real hardware)

The mouse itself needs no driver on Linux; this app only adds the tray battery and settings UI. The protocol layer is identical, but the Linux port could only be verified in a VM without the mouse attached. Reports from real hardware are very welcome.

```bash
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
./linux/kurulum.sh        # udev rule (sudo), pip packages, .desktop + autostart, then starts it
```

Debian/Ubuntu packages for the tray backend and the guide window: `sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 python3-tk`; on GNOME also enable the *AppIndicator* extension. Uninstall with `./linux/kurulum.sh -u`. Config lives in `~/.config/clawtray/`.

## Good to know

- **Does not run alongside the CrossFire software.** If both talk to the mouse at the same time the CrossFire app crashes (the mouse is unaffected), so the tray app pauses itself while CrossFire is running (icon shows `!`). You can uninstall CrossFire; this app does not depend on it.
- Settings cannot be written while the mouse is asleep (idle for about a minute): the icon shows `II` and recovers as soon as you move the mouse.
- If anything goes wrong, *Restore* in the vendor software resets the mouse to factory defaults.
- Macros and button remapping are deliberately out of scope.

## How it works

The mouse (or its receiver) exposes a HID collection with usage page `0xFF02` under VID `0x3554`. Each command is a 17 byte output report; the reply comes back as an input report in the same layout:

```
[0]  = 0x08 report id      [1]     = command      [2]  = status
[3]  = address high        [4]     = address low  [5]  = length (up to 10)
[6..15] = data             [16]    = chk, chk = (0x55 - sum(bytes 0..15)) & 0xFF
```

| Command | Purpose |
|---|---|
| `0x03` | Is the mouse online |
| `0x04` | Battery: `[6]` level %, `[7]` charging |
| `0x07` / `0x08` | Write / read the settings flash |
| `0x12` | Version |
| `0x16` / `0x17` | Long range mode set / get |

In the settings flash every single byte field is stored as the pair `value, chk` with `chk = (0x55 - value) & 0xFF`; multi byte groups end with `chk = (0x55 - sum(values)) & 0xFF`:

| Address | Field |
|---|---|
| `0x00` | Report rate (1 = 1000 Hz, 2 = 500, 4 = 250, 8 = 125) |
| `0x02` / `0x04` | DPI stage count / active stage |
| `0x0C + 4i` | Stage i DPI: `x, y, ex, chk`; code from the PAW3325 table, above 4000 DPI `ex = 0x11` and table[DPI/2] |
| `0x2C + 4i` | Stage i colour `r, g, b, chk` |
| `0x4C` … `0x52` | DPI indicator LED: mode, brightness, speed, enable |
| `0xA0` … `0xA7` | Light strip: mode, r, g, b, speed, brightness, chk; `0xA7` enable |
| `0xA9` | Debounce (ms) |
| `0xAB` / `0xAF` / `0xB1` | Motion sync / angle snapping / ripple control |
| `0xAD` | LEDs off time when idle (×10 s) |
| `0xB3` | LEDs off while moving |
| `0xB5` / `0xB7` | Peak performance enable / time (×10 s) |

Field names come from the debug symbols shipped with the vendor software (`MouseConfig`, `LedBar`, `DPILed`, `DPIConfig`, `BatteryStatus`). `claw_proto.py` is the whole protocol layer and can be used on its own.

## Files

| File | |
|---|---|
| `claw_tray.py` | Tray app, menu, presets, help, guide window |
| `claw_proto.py` | Protocol layer (hidapi) and PAW3325 DPI table |
| `claw_lang.py` | All UI text in ten languages |
| `kurulum.ps1` | Creates / removes Windows shortcuts |
| `linux/kurulum.sh`, `linux/70_clawcrossfire.rules` | Linux installer and udev rule |
| `claw.ico` / `claw.png` | Application icon (Windows / Linux) |
| `build.ps1` | Builds `ClawTray.exe` and the release zip with PyInstaller |

## License

MIT, see [LICENSE](LICENSE).
