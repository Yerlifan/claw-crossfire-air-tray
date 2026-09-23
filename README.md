# Claw CrossFire AIR — tray control

🇹🇷 **[Türkçe](README.tr.md)** · 🇬🇧 English

A small Windows system-tray app for the **Claw CrossFire AIR V1** wireless mouse that needs neither the vendor's software nor its DLL.

- **Battery percentage** as a big number in the tray; Windows notifications when charging starts/stops and at 20 % / 10 %
- **Every setting in the right-click menu:** DPI stages, report rate, debounce, motion sync, angle snapping, ripple control, peak performance, lighting mode / colour / brightness / speed, long-range mode
- **Presets:** one click for "CS2 (800 DPI)" or "Desktop (1600 DPI)"
- Talks to the mouse **directly over HID** — no `HIDUsb.dll`, no CrossFire software
- Icon hides when the mouse is not connected; starts with Windows

> Not affiliated with the manufacturer. The protocol was reverse-engineered by observing the vendor software and has been tested only on the **CrossFire AIR V1** (PixArt PAW3325, firmware v2.0, 2.4 GHz receiver). Use at your own risk. The menu text is Turkish.

## Install

### Option A — ready-made executable (no Python needed)

1. Download `ClawTray-<version>-win64.zip` from the [Releases](https://github.com/Yerlifan/claw-crossfire-air-tray/releases) page and unzip it anywhere (e.g. `C:\Users\<you>\ClawTray`).
2. Run `ClawTray.exe`. The icon appears in the tray (possibly under the `^` overflow).
3. Optional — shortcuts in the Start menu, on the desktop and at Windows startup:
   ```powershell
   powershell -ExecutionPolicy Bypass -File kurulum.ps1
   ```

Windows SmartScreen may warn about an unsigned executable the first time; choose *More info → Run anyway*, or use option B.

### Option B — from source

Requirements: Windows 10/11, Python 3.10+.

```powershell
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
pip install -r requirements.txt
pythonw claw_tray.py
```

`kurulum.ps1` works here too (it uses `pythonw` when there is no `ClawTray.exe` next to it). To uninstall: `kurulum.ps1 -Kaldir`, then delete the folder — nothing else is written to the system.

Print the current state from a terminal: `python claw_tray.py --durum` (or `ClawTray.exe --durum`).

## Good to know

- **Does not run alongside the CrossFire software.** If both talk to the mouse at the same time the CrossFire app crashes (the mouse is unaffected), so the tray app pauses itself while CrossFire is running (icon shows `II`). You can uninstall CrossFire; this app does not depend on it.
- Settings cannot be written while the mouse is asleep (idle for ~1 min): the icon turns grey `--` and recovers as soon as you move the mouse.
- Every write is read back from the mouse and verified. If anything goes wrong, *Restore* in the vendor software resets the mouse to factory defaults.
- Macros and button remapping are deliberately out of scope.

## How it works

The mouse (or its receiver) exposes a HID collection with usage page `0xFF02` under VID `0x3554`. Each command is a 17-byte output report; the reply comes back as an input report in the same layout:

```
[0]=0x08 report id   [1]=command   [2]=status   [3..4]=address (big-endian)
[5]=length (≤10)     [6..15]=data                [16]=0x55 − sum(0..15)
```

| Command | Purpose |
|---|---|
| `0x03` | Is the mouse online |
| `0x04` | Battery: `[6]` level %, `[7]` charging |
| `0x07` / `0x08` | Write / read the settings flash |
| `0x12` | Version |
| `0x16` / `0x17` | Long-range mode set / get |

In the settings flash every single-byte field is stored as the pair `(value, 0x55 − value)`; multi-byte groups end with `0x55 − sum`:

| Address | Field |
|---|---|
| `0x00` | Report rate (1 = 1000 Hz, 2 = 500, 4 = 250, 8 = 125) |
| `0x02` / `0x04` | DPI stage count / active stage |
| `0x0C + 4i` | Stage i DPI: `x, y, ex, checksum` — code from the PAW3325 table; above 4000 DPI `ex = 0x11` and table[DPI/2] |
| `0x2C + 4i` | Stage i colour `r, g, b, checksum` |
| `0x4C` … `0x52` | DPI indicator LED: mode, brightness, speed, enable |
| `0xA0` … `0xA7` | Light strip: mode, r, g, b, speed, brightness, checksum; `0xA7` enable |
| `0xA9` | Debounce (ms) |
| `0xAB` / `0xAF` / `0xB1` | Motion sync / angle snapping / ripple control |
| `0xAD` | LEDs-off time when idle (×10 s) |
| `0xB3` | LEDs off while moving |
| `0xB5` / `0xB7` | Peak performance enable / time (×10 s) |

Field names come from the debug symbols shipped with the vendor software (`MouseConfig`, `LedBar`, `DPILed`, `DPIConfig`, `BatteryStatus`). `claw_proto.py` is the whole protocol layer and can be used on its own.

## Files

| File | |
|---|---|
| `claw_tray.py` | Tray app and menu |
| `claw_proto.py` | Protocol layer (hidapi) and PAW3325 DPI table |
| `kurulum.ps1` | Creates / removes shortcuts |
| `claw.ico` | Shortcut icon |
| `build.ps1` | Builds `ClawTray.exe` with PyInstaller |

## License

MIT — see [LICENSE](LICENSE).
