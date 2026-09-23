# -*- coding: utf-8 -*-
"""Claw CrossFire AIR V1: system tray control / sistem tepsisi denetimi.

Battery percentage + every mouse setting (DPI, report rate, debounce, sensor, lighting, long range)
in the right click menu. Talks to the mouse directly over USB HID (claw_proto.py, hidapi); the vendor
software is not needed. Pauses itself while the vendor app is running to avoid conflicts.
UI language: Turkish if the Windows UI language is Turkish, otherwise English; switchable from the menu.

Flash layout (each field: value, 0x55 minus value):
  0x00 report rate | 0x02 stage count | 0x04 active stage | 0x0A LOD
  0x0C+4i DPI (x, y, ex, chk) | 0x2C+4i stage colour (r, g, b, chk)
  0x4C/4E/50/52 DPI LED: mode, brightness, speed, enable
  0xA0 light strip: mode, r, g, b, speed, brightness, chk | 0xA7 enable
  0xA9 debounce | 0xAB motion sync | 0xAD LEDs off time (x10 s) | 0xAF angle snapping
  0xB1 ripple | 0xB3 LEDs off while moving | 0xB5 peak performance | 0xB7 its time (x10 s)
"""
import ctypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time

IS_WIN = sys.platform == "win32"
if IS_WIN:
    import ctypes.wintypes as w
else:
    import fcntl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import claw_proto as cp  # noqa: E402

VENDOR_EXE = "CrossFire AIR V1.exe"
BATTERY_INTERVAL = 5      # s
CONFIG_INTERVAL = 30      # s
DEVICE_POLL = 60          # s, while no mouse is connected
if IS_WIN:
    APPDIR = os.path.join(os.environ.get("LOCALAPPDATA", HERE), "ClawBattery")
else:
    APPDIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "clawtray")
LOG = os.path.join(APPDIR, "log.txt")
CONFIG = os.path.join(APPDIR, "config.json")

# addresses
A_RATE, A_MAXDPI, A_CURDPI = 0x00, 0x02, 0x04
A_DPI, A_DPICOLOR = 0x0C, 0x2C
A_DL_MODE, A_DL_BRIGHT, A_DL_SPEED, A_DL_EN = 0x4C, 0x4E, 0x50, 0x52
A_LED, A_LED_EN = 0xA0, 0xA7
A_DEBOUNCE, A_MOTION, A_LEDOFF, A_ANGLE = 0xA9, 0xAB, 0xAD, 0xAF
A_RIPPLE, A_MOVEOFF, A_PERF_EN, A_PERF_TIME = 0xB1, 0xB3, 0xB5, 0xB7
FLASH_LEN = 0xC0

RATES = [(1, "1000 Hz"), (2, "500 Hz"), (4, "250 Hz"), (8, "125 Hz")]
DEBOUNCES = [2, 4, 6, 8, 10, 12]
DPI_CHOICES = [400, 800, 1000, 1200, 1600, 2000, 2400, 3200, 4000, 4800, 6400, 8000, 10000]
PERF_TIMES = [3, 6, 12, 30, 60, 90]                      # x10 s
LEDOFF_TIMES = [1, 3, 6, 30, 60, 90, 120, 180, 240]      # x10 s
LED_MODE_CODES = [1, 2, 3, 4, 5, 6]
LED_COLORS = [("red", (255, 0, 0)), ("green", (0, 255, 0)), ("blue", (0, 0, 255)),
              ("white", (255, 255, 255)), ("purple", (160, 0, 255)), ("cyan", (0, 255, 255)),
              ("yellow", (255, 255, 0)), ("orange", (255, 128, 0)), ("pink", (255, 0, 160))]
DPILED_MODE_CODES = [1, 2]
DPI_TABLE = cp.DPI_TABLE
DPI_REVERSE = cp.DPI_REVERSE

# i18n
STRINGS = {
    "tr": {
        "app": "Claw fare",
        "title_paused": "Claw fare: CrossFire açık, duraklatıldı",
        "title_asleep": "Claw fare: uykuda (hareket ettirin)",
        "title_ok": "Claw fare: %{lvl}",
        "charging": " (şarj oluyor)",
        "dpi_suffix": ", {dpi} DPI",
        "n_charge_on": "Şarj başladı (%{lvl})",
        "n_charge_off": "Şarj kablosu çıktı (%{lvl})",
        "n_full": "Pil doldu (%100), kabloyu çıkarabilirsiniz",
        "n_low": "Pil %{lvl}, şarj edin",
        "n_write_fail": "Ayar yazılamadı: fare uykuda ya da CrossFire açık olabilir",
        "n_preset": "{name} ön ayarı uygulandı ({dpi} DPI)",
        "presets": "Ön ayarlar", "preset_cs2": "CS2 (800 DPI)", "preset_desk": "Masaüstü (1600 DPI)",
        "dpi": "DPI", "active_stage": "Aktif kademe", "stage_n": "Kademe {n}: {dpi} DPI",
        "stage_value": "Kademe {n} değeri ({dpi})", "stage_count": "Kademe sayısı",
        "rate": "Rapor hızı", "debounce": "Debounce", "ms": "{n} ms",
        "sensor": "Sensör", "motion": "Motion sync", "angle": "Açı düzeltme (angle snapping)",
        "ripple": "Ripple kontrolü", "perf": "Maksimum performans", "off": "Kapalı",
        "sec": "{n} sn", "min": "{n} dk",
        "light": "Işık", "mode": "Mod", "color": "Renk", "brightness": "Parlaklık", "speed": "Hız",
        "moveoff": "Hareket ederken ışığı kapat", "ledoff": "Hareketsiz kalınca kapanma süresi",
        "dpiled": "DPI gösterge ışığı",
        "led1": "Gökkuşağı Akış", "led2": "Tek Renk Nefes", "led3": "Gökkuşağı Sabit",
        "led4": "Neon", "led5": "Gökkuşağı Yanıp Sönme", "led6": "Çok Renkli Sabit",
        "dl1": "Sabit ışık", "dl2": "Yanıp sönme",
        "red": "Kırmızı", "green": "Yeşil", "blue": "Mavi", "white": "Beyaz", "purple": "Mor",
        "cyan": "Turkuaz", "yellow": "Sarı", "orange": "Turuncu", "pink": "Pembe",
        "longrange": "Uzun menzil modu", "language": "Dil / Language",
        "refresh": "Şimdi yenile", "quit": "Çıkış",
    },
    "en": {
        "app": "Claw mouse",
        "title_paused": "Claw mouse: CrossFire is running, paused",
        "title_asleep": "Claw mouse: asleep (move it)",
        "title_ok": "Claw mouse: {lvl}%",
        "charging": " (charging)",
        "dpi_suffix": ", {dpi} DPI",
        "n_charge_on": "Charging started ({lvl}%)",
        "n_charge_off": "Charging cable unplugged ({lvl}%)",
        "n_full": "Battery full (100%), you can unplug the cable",
        "n_low": "Battery {lvl}%, please charge",
        "n_write_fail": "Could not write the setting: mouse asleep or CrossFire running",
        "n_preset": "{name} preset applied ({dpi} DPI)",
        "presets": "Presets", "preset_cs2": "CS2 (800 DPI)", "preset_desk": "Desktop (1600 DPI)",
        "dpi": "DPI", "active_stage": "Active stage", "stage_n": "Stage {n}: {dpi} DPI",
        "stage_value": "Stage {n} value ({dpi})", "stage_count": "Number of stages",
        "rate": "Report rate", "debounce": "Debounce", "ms": "{n} ms",
        "sensor": "Sensor", "motion": "Motion sync", "angle": "Angle snapping",
        "ripple": "Ripple control", "perf": "Peak performance", "off": "Off",
        "sec": "{n} s", "min": "{n} min",
        "light": "Lighting", "mode": "Mode", "color": "Colour", "brightness": "Brightness", "speed": "Speed",
        "moveoff": "Lights off while moving", "ledoff": "Lights off delay when idle",
        "dpiled": "DPI indicator light",
        "led1": "Rainbow Wave", "led2": "Single Colour Breathing", "led3": "Rainbow Fixed",
        "led4": "Neon", "led5": "Rainbow Flicker", "led6": "Multicolour Fixed",
        "dl1": "Steady", "dl2": "Flicker",
        "red": "Red", "green": "Green", "blue": "Blue", "white": "White", "purple": "Purple",
        "cyan": "Cyan", "yellow": "Yellow", "orange": "Orange", "pink": "Pink",
        "longrange": "Long range mode", "language": "Language / Dil",
        "refresh": "Refresh now", "quit": "Quit",
    },
}
LANG = {"code": "en"}


def t(key, **kw):
    s = STRINGS.get(LANG["code"], STRINGS["en"]).get(key) or STRINGS["en"].get(key, key)
    return s.format(**kw) if kw else s


def duration(x10s):
    """x10 s to '30 sn' / '1 dk' in the current language."""
    secs = x10s * 10
    return t("sec", n=secs) if secs < 60 else t("min", n=secs // 60)


def system_language():
    try:
        if IS_WIN:
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            return "tr" if lang_id == 0x1F else "en"
        code = os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or ""
        return "tr" if code.lower().startswith("tr") else "en"
    except Exception:
        return "en"


def load_config():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        os.makedirs(APPDIR, exist_ok=True)
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log("config save error: %r" % e)


def log(msg):
    try:
        os.makedirs(APPDIR, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + chr(10))
    except Exception:
        pass


def dpi_encode(dpi):
    """CrossFire rule: <=4000 direct, above that DPIex=0x11 and table[dpi/2]."""
    if dpi <= 4000:
        return DPI_TABLE[dpi], 0x00
    return DPI_TABLE[dpi // 2], 0x11


def dpi_decode(x, ex):
    base = DPI_REVERSE.get(x)
    if base is None:
        return None
    return base * 2 if ex == 0x11 else base


# is the vendor app running (Windows only)
if IS_WIN:
    class _PE32(ctypes.Structure):
        _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)), ("th32ModuleID", w.DWORD),
                    ("cntThreads", w.DWORD), ("th32ParentProcessID", w.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", w.DWORD), ("szExeFile", ctypes.c_char * 260)]

    _k32 = ctypes.windll.kernel32
    _k32.CreateToolhelp32Snapshot.restype = w.HANDLE


def vendor_running():
    if not IS_WIN:
        return False
    snap = _k32.CreateToolhelp32Snapshot(0x2, 0)
    e = _PE32()
    e.dwSize = ctypes.sizeof(_PE32)
    found = False
    ok = _k32.Process32First(snap, ctypes.byref(e))
    while ok:
        if e.szExeFile.decode(errors="ignore").lower() == VENDOR_EXE.lower():
            found = True
            break
        ok = _k32.Process32Next(snap, ctypes.byref(e))
    _k32.CloseHandle(snap)
    return found


_vr_cache = {"t": 0.0, "v": False}


def vendor_running_cached(max_age=3.0):
    now = time.time()
    if now - _vr_cache["t"] > max_age:
        _vr_cache["v"], _vr_cache["t"] = vendor_running(), now
    return _vr_cache["v"]


# mouse state
class Mouse:
    def __init__(self):
        self.lock = threading.RLock()
        self.path = None
        self.flash = None
        self.battery = None        # (level, charging)
        self.long_range = None
        self.status = "nodevice"   # nodevice | paused | asleep | ok
        self._cfg_time = 0
        self._paths = []
        self._paths_time = 0

    # -- reading --
    def _pick_path(self):
        """HID enumeration is slow (~100-300 ms): cache 30 s, rescan at once after a failure."""
        now = time.time()
        if not self._paths or now - self._paths_time > 30:
            self._paths, self._paths_time = cp.device_paths(), now
        self.path = self._paths[0] if self._paths else None
        return self._paths

    def poll(self, force_config=False):
        with self.lock:
            paths = self._pick_path()
            if not paths:
                self.status = "nodevice"
                return
            if vendor_running_cached():
                self.status = "paused"
                return
            got = None
            for pth in paths:
                try:
                    b = cp.battery(pth)
                    if b and b[0] > 0:
                        got = b
                        self.path = pth
                        break
                except Exception as e:
                    log("battery error: %r" % e)
            if got is None:
                self.status = "asleep"
                self._paths_time = 0
                return
            self.battery = got
            self.status = "ok"
            if force_config or self.flash is None or time.time() - self._cfg_time > CONFIG_INTERVAL:
                self.read_config()

    def read_config(self):
        with self.lock:
            fl = cp.read_flash(self.path, 0, FLASH_LEN)
            if fl:
                self.flash = bytearray(fl)
                self._cfg_time = time.time()
            lr = cp.get_long_range(self.path)
            if lr is not None:
                self.long_range = lr

    def byte(self, addr):
        if self.flash is None:
            return None
        v, c = self.flash[addr], self.flash[addr + 1]
        return v if (v + c) & 0xFF == 0x55 else None

    def dpi(self, i):
        if self.flash is None:
            return None
        x, _, ex, _ = self.flash[A_DPI + 4 * i:A_DPI + 4 * i + 4]
        return dpi_decode(x, ex)

    def led(self):
        if self.flash is None:
            return None
        mode, r, g, b, speed, bright = self.flash[A_LED:A_LED + 6]
        return {"mode": mode, "rgb": (r, g, b), "speed": speed, "bright": bright, "en": self.byte(A_LED_EN)}

    # -- writing --
    def _can_write(self):
        return self.status == "ok" and self.path is not None and not vendor_running_cached()

    def set_byte(self, addr, val):
        with self.lock:
            if not self._can_write():
                return False
            ok = cp.write_byte(self.path, addr, val)
            if ok:
                self.flash[addr], self.flash[addr + 1] = val & 0xFF, (0x55 - val) & 0xFF
            log("write 0x%02X=%d => %s" % (addr, val, ok))
            return ok

    def set_group(self, addr, vals):
        """Multi byte field: values plus checksum (0x55 minus sum)."""
        with self.lock:
            if not self._can_write():
                return False
            data = bytes(vals) + bytes([(0x55 - sum(vals)) & 0xFF])
            ok = cp.write_flash(self.path, addr, data) and cp.read_flash(self.path, addr, len(data)) == data
            if ok:
                self.flash[addr:addr + len(data)] = data
            log("write 0x%02X=%s => %s" % (addr, data.hex(" "), ok))
            return ok

    def set_dpi(self, i, dpi):
        x, ex = dpi_encode(dpi)
        return self.set_group(A_DPI + 4 * i, [x, x, ex])

    def set_led(self, **kw):
        cur = self.led()
        if cur is None:
            return False
        cur.update(kw)
        r, g, b = cur["rgb"]
        return self.set_group(A_LED, [cur["mode"], r, g, b, cur["speed"], cur["bright"]])

    def set_long_range(self, on):
        with self.lock:
            if not self._can_write():
                return False
            ok = cp.set_long_range(self.path, on)
            if ok:
                lr = cp.get_long_range(self.path)
                if lr is not None:
                    self.long_range = lr
            log("long range=%s => %s" % (on, ok))
            return ok


# icon
def make_icon(level, charging, paused=False):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if level is None:
        col, txt, fg = (110, 110, 110), ("II" if paused else "?"), (235, 235, 235)
    else:
        col = (60, 170, 60) if level > 33 else (235, 150, 30) if level > 15 else (220, 50, 50)
        txt, fg = str(level), (255, 255, 255)
    d.rounded_rectangle((0, 0, 63, 63), radius=12, fill=col)
    if charging:
        d.rounded_rectangle((0, 0, 63, 63), radius=12, outline=(255, 225, 0), width=5)
    size = 46 if len(txt) <= 2 else 34
    font = None
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "NotoSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(name, size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((64 - tw) / 2 - bbox[0], (64 - th) / 2 - bbox[1] - 2), txt, font=font, fill=fg)
    if charging:
        d.polygon([(52, 38), (46, 52), (51, 52), (49, 62), (58, 48), (53, 48)], fill=(255, 225, 0))
    return img


_lock_handle = None


def single_instance():
    """Exit quietly if another copy is already running (no duplicate tray icons)."""
    global _lock_handle
    if IS_WIN:
        _k32.CreateMutexW(None, False, "ClawTray_SingleInstance")
        return _k32.GetLastError() != 183   # ERROR_ALREADY_EXISTS
    try:
        os.makedirs(APPDIR, exist_ok=True)
        _lock_handle = open(os.path.join(APPDIR, "lock"), "w")
        fcntl.flock(_lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


# app
def main():
    cfg = load_config()
    LANG["code"] = cfg.get("lang") or system_language()
    for i, a in enumerate(sys.argv):
        if a == "--lang" and i + 1 < len(sys.argv) and sys.argv[i + 1] in STRINGS:
            LANG["code"] = sys.argv[i + 1]

    m = Mouse()
    if "--durum" in sys.argv or "--status" in sys.argv:
        m.poll(force_config=True)
        print("status:", m.status, "| battery:", m.battery, "| long range:", m.long_range)
        if m.flash:
            n = m.byte(A_MAXDPI) or 0
            print("rate code:", m.byte(A_RATE), "| stages:", n, "| active:", m.byte(A_CURDPI),
                  "| DPI:", [m.dpi(i) for i in range(n)])
            print("debounce:", m.byte(A_DEBOUNCE), "| motion:", m.byte(A_MOTION), "| angle:", m.byte(A_ANGLE),
                  "| ripple:", m.byte(A_RIPPLE), "| perf:", m.byte(A_PERF_EN), m.byte(A_PERF_TIME))
            print("light:", m.led(), "| off delay:", m.byte(A_LEDOFF), "| off while moving:", m.byte(A_MOVEOFF))
            print("DPI LED: mode", m.byte(A_DL_MODE), "enabled", m.byte(A_DL_EN))
        return
    if not single_instance():
        return

    import pystray
    from pystray import Menu, MenuItem as Item

    icon = pystray.Icon("ClawTray", make_icon(None, False), t("app"))
    st = {"charging": None, "warned": set()}
    last = {"icon": None, "menu": None, "title": None, "visible": None}

    def notify(msg):
        try:
            if not IS_WIN and shutil.which("notify-send"):
                subprocess.Popen(["notify-send", "-a", t("app"), t("app"), msg])
                return
            icon.notify(msg, t("app"))
        except Exception as e:
            log("notify error: %r" % e)

    def title_text():
        if m.status == "paused":
            return t("title_paused")
        if m.status == "asleep":
            return t("title_asleep")
        if m.status == "ok" and m.battery:
            lvl, chg = m.battery
            n = m.byte(A_CURDPI)
            dpi = m.dpi(n) if n is not None else None
            s = t("title_ok", lvl=lvl) + (t("charging") if chg else "")
            return s + (t("dpi_suffix", dpi=dpi) if dpi else "")
        return t("app")

    def redraw(force=False):
        vis = m.status != "nodevice"
        if vis != last["visible"]:
            icon.visible = vis
            last["visible"] = vis
        if not vis:
            return
        isig = (m.status, m.battery)
        if isig != last["icon"]:
            if m.status == "ok" and m.battery:
                icon.icon = make_icon(m.battery[0], m.battery[1])
            else:
                icon.icon = make_icon(None, False, paused=(m.status == "paused"))
            last["icon"] = isig
        ttl = title_text()
        if ttl != last["title"]:
            icon.title = ttl
            last["title"] = ttl
        msig = (m.status, bytes(m.flash) if m.flash else None, m.long_range, LANG["code"])
        if force or msig != last["menu"]:
            try:
                icon.update_menu()
            except Exception:
                pass
            last["menu"] = msig

    def battery_notifications():
        if m.status != "ok" or not m.battery:
            return
        lvl, chg = m.battery
        if st["charging"] is not None and chg != st["charging"]:
            notify(t("n_charge_on", lvl=lvl) if chg else t("n_charge_off", lvl=lvl))
            st["warned"].discard("full")
        if chg and lvl >= 100 and "full" not in st["warned"]:
            notify(t("n_full"))
            st["warned"].add("full")
        if not chg:
            for th in (20, 10):
                key = "low%d" % th
                if lvl <= th and key not in st["warned"]:
                    notify(t("n_low", lvl=lvl))
                    st["warned"].add(key)
                elif lvl > th + 5:
                    st["warned"].discard(key)
        st["charging"] = chg

    def refresh(force=False):
        try:
            m.poll(force_config=force)
            battery_notifications()
        except Exception as e:
            log("refresh error: %r" % e)
        redraw()

    def loop():
        while True:
            refresh()
            time.sleep(DEVICE_POLL if m.status == "nodevice" else BATTERY_INTERVAL)

    # -- menu helpers --
    def ready(_item=None):
        return m.status == "ok" and m.flash is not None

    def act(fn):
        """Run a write off the UI thread; notify on failure; then refresh the menu."""
        def work():
            ok = False
            try:
                ok = fn()
            except Exception as e:
                log("action error: %r" % e)
            if not ok:
                notify(t("n_write_fail"))
            redraw()

        def run(_icon, _item):
            threading.Thread(target=work, daemon=True).start()
        return run

    def L(key, **kw):
        """Menu text evaluated at render time so language switches apply instantly."""
        return lambda _i: t(key, **kw)

    def radio(text, getter, value, setter):
        return Item(text, act(lambda: setter(value)), checked=lambda _i: getter() == value, radio=True, enabled=ready)

    def toggle(key, addr):
        return Item(L(key), act(lambda: m.set_byte(addr, 0 if m.byte(addr) else 1)),
                    checked=lambda _i: bool(m.byte(addr)), enabled=ready)

    def stage_menu(i):
        items = [radio("%d DPI" % d, lambda i=i: m.dpi(i), d, lambda v, i=i: m.set_dpi(i, v)) for d in DPI_CHOICES]
        return Item(lambda _i, i=i: t("stage_value", n=i + 1, dpi=m.dpi(i) or "?"), Menu(*items),
                    visible=lambda _i, i=i: (m.byte(A_MAXDPI) or 0) > i, enabled=ready)

    def active_stage_items():
        return [Item(lambda _i, i=i: t("stage_n", n=i + 1, dpi=m.dpi(i) or "?"),
                     act(lambda i=i: m.set_byte(A_CURDPI, i)),
                     checked=lambda _i, i=i: m.byte(A_CURDPI) == i, radio=True,
                     visible=lambda _i, i=i: (m.byte(A_MAXDPI) or 0) > i, enabled=ready) for i in range(6)]

    def set_perf(code):
        if code == 0:
            return m.set_byte(A_PERF_EN, 0)
        return m.set_byte(A_PERF_TIME, code) and m.set_byte(A_PERF_EN, 1)

    def perf_state():
        return (m.byte(A_PERF_TIME) or 0) if m.byte(A_PERF_EN) else 0

    def set_led_mode(code):
        if code == 0:
            return m.set_byte(A_LED_EN, 0)
        return m.set_led(mode=code) and m.set_byte(A_LED_EN, 1)

    def led_mode_state():
        led = m.led()
        return led["mode"] if led and led["en"] else 0

    def set_dpiled(code):
        if code == 0:
            return m.set_byte(A_DL_EN, 0)
        return m.set_byte(A_DL_MODE, code) and m.set_byte(A_DL_EN, 1)

    def dpiled_state():
        return (m.byte(A_DL_MODE) or 0) if m.byte(A_DL_EN) else 0

    def preset(dpi, name_key):
        def run():
            n = m.byte(A_MAXDPI) or 0
            idx = next((i for i in range(n) if m.dpi(i) == dpi), None)
            if idx is None:
                idx = 0
                if not m.set_dpi(0, dpi):
                    return False
            ok = m.set_byte(A_CURDPI, idx)
            ok = m.set_byte(A_RATE, 1) and ok
            ok = m.set_byte(A_DEBOUNCE, 4) and ok
            ok = m.set_byte(A_ANGLE, 0) and ok
            ok = m.set_byte(A_RIPPLE, 0) and ok
            ok = m.set_byte(A_MOTION, 1) and ok
            ok = set_perf(6) and ok
            if ok:
                notify(t("n_preset", name=t(name_key).split(" (")[0], dpi=dpi))
            return ok
        return run

    def set_language(code):
        LANG["code"] = code
        cfg["lang"] = code
        save_config(cfg)
        redraw(force=True)

    dpi_menu = Menu(
        Item(L("active_stage"), Menu(*active_stage_items()), enabled=ready),
        Menu.SEPARATOR,
        *[stage_menu(i) for i in range(6)],
        Menu.SEPARATOR,
        Item(L("stage_count"), Menu(*[radio(str(n), lambda: m.byte(A_MAXDPI), n, lambda v: m.set_byte(A_MAXDPI, v))
                                      for n in range(1, 7)]), enabled=ready),
    )
    sensor_menu = Menu(
        toggle("motion", A_MOTION),
        toggle("angle", A_ANGLE),
        toggle("ripple", A_RIPPLE),
        Menu.SEPARATOR,
        Item(L("perf"), Menu(
            radio(L("off"), perf_state, 0, set_perf),
            *[radio(lambda _i, c=c: duration(c), perf_state, c, set_perf) for c in PERF_TIMES]), enabled=ready),
    )
    light_menu = Menu(
        Item(L("mode"), Menu(radio(L("off"), led_mode_state, 0, set_led_mode),
                             *[radio(L("led%d" % c), led_mode_state, c, set_led_mode) for c in LED_MODE_CODES]),
             enabled=ready),
        Item(L("color"), Menu(*[radio(L(k), lambda: (m.led() or {}).get("rgb"), rgb, lambda v: m.set_led(rgb=v))
                                for k, rgb in LED_COLORS]), enabled=ready),
        Item(L("brightness"), Menu(*[radio(str(n), lambda: (m.led() or {}).get("bright"), n - 1,
                                           lambda v: m.set_led(bright=v)) for n in range(1, 11)]), enabled=ready),
        Item(L("speed"), Menu(*[radio(str(n), lambda: (m.led() or {}).get("speed"), n - 1,
                                      lambda v: m.set_led(speed=v)) for n in range(1, 11)]), enabled=ready),
        Menu.SEPARATOR,
        toggle("moveoff", A_MOVEOFF),
        Item(L("ledoff"), Menu(*[radio(lambda _i, c=c: duration(c), lambda: m.byte(A_LEDOFF), c,
                                       lambda v: m.set_byte(A_LEDOFF, v)) for c in LEDOFF_TIMES]), enabled=ready),
        Menu.SEPARATOR,
        Item(L("dpiled"), Menu(radio(L("off"), dpiled_state, 0, set_dpiled),
                               *[radio(L("dl%d" % c), dpiled_state, c, set_dpiled) for c in DPILED_MODE_CODES]),
             enabled=ready),
    )
    icon.menu = Menu(
        Item(lambda _i: title_text(), None, enabled=False),
        Menu.SEPARATOR,
        Item(L("presets"), Menu(Item(L("preset_cs2"), act(preset(800, "preset_cs2")), enabled=ready),
                                Item(L("preset_desk"), act(preset(1600, "preset_desk")), enabled=ready)),
             enabled=ready),
        Item(L("dpi"), dpi_menu, enabled=ready),
        Item(L("rate"), Menu(*[radio(txt, lambda: m.byte(A_RATE), c, lambda v: m.set_byte(A_RATE, v))
                               for c, txt in RATES]), enabled=ready),
        Item(L("debounce"), Menu(*[radio(L("ms", n=d), lambda: m.byte(A_DEBOUNCE), d,
                                         lambda v: m.set_byte(A_DEBOUNCE, v)) for d in DEBOUNCES]), enabled=ready),
        Item(L("sensor"), sensor_menu, enabled=ready),
        Item(L("light"), light_menu, enabled=ready),
        Item(L("longrange"), act(lambda: m.set_long_range(not m.long_range)),
             checked=lambda _i: bool(m.long_range), enabled=ready),
        Menu.SEPARATOR,
        Item(L("language"), Menu(
            Item("Türkçe", lambda _ic, _it: set_language("tr"), checked=lambda _i: LANG["code"] == "tr", radio=True),
            Item("English", lambda _ic, _it: set_language("en"), checked=lambda _i: LANG["code"] == "en", radio=True))),
        Item(L("refresh"), lambda _ic, _it: threading.Thread(target=refresh, args=(True,), daemon=True).start()),
        Item(L("quit"), lambda ic, _it: ic.stop()),
    )

    def setup(ic):
        ic.visible = bool(cp.device_paths())
        threading.Thread(target=loop, daemon=True).start()

    log("claw_tray started (lang=%s)" % LANG["code"])
    icon.run(setup=setup)


if __name__ == "__main__":
    main()
