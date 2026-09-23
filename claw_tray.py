# -*- coding: utf-8 -*-
"""Claw CrossFire AIR V1 - sistem tepsisi denetim merkezi.

Pil yüzdesi + farenin ayarları (DPI, rapor hızı, debounce, sensör, ışık, uzun menzil)
sağ tık menüsünden. Fareyle doğrudan USB üzerinden konuşur (claw_proto.py, hidapi);
CrossFire yazılımına ihtiyaç duymaz. CrossFire açıkken çakışmayı önlemek için kendini duraklatır.

Flash düzeni (her alan: değer, 0x55-değer):
  0x00 rapor hızı | 0x02 kademe sayısı | 0x04 aktif kademe | 0x0A LOD
  0x0C+4i DPI (x, y, ex, sağlama) | 0x2C+4i kademe rengi (r, g, b, sağlama)
  0x4C/4E/50/52 DPI ışığı: mod, parlaklık, hız, etkin
  0xA0 ışık şeridi: mod, r, g, b, hız, parlaklık, sağlama | 0xA7 etkin
  0xA9 debounce | 0xAB motion sync | 0xAD ışık kapanma süresi (x10 sn) | 0xAF açı düzeltme
  0xB1 ripple | 0xB3 hareket ederken ışığı kapat | 0xB5 maks. performans | 0xB7 süresi (x10 sn)
"""
import ctypes
import ctypes.wintypes as w
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import claw_proto as cp  # noqa: E402

VENDOR_EXE = "CrossFire AIR V1.exe"
BATTERY_INTERVAL = 5      # sn
CONFIG_INTERVAL = 30      # sn
DEVICE_POLL = 60          # sn, fare yokken
LOG = os.path.join(os.environ.get("LOCALAPPDATA", HERE), "ClawBattery", "log.txt")

# ---- adresler -------------------------------------------------------------
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
PERF_TIMES = [(3, "30 sn"), (6, "1 dk"), (12, "2 dk"), (30, "5 dk"), (60, "10 dk"), (90, "15 dk")]
LEDOFF_TIMES = [(1, "10 sn"), (3, "30 sn"), (6, "1 dk"), (30, "5 dk"), (60, "10 dk"),
                (90, "15 dk"), (120, "20 dk"), (180, "30 dk"), (240, "40 dk")]
LED_MODES = [(1, "Gökkuşağı Akış"), (2, "Tek Renk Nefes"), (3, "Gökkuşağı Sabit"),
             (4, "Neon"), (5, "Gökkuşağı Yanıp Sönme"), (6, "Çok Renkli Sabit")]
LED_COLORS = [("Kırmızı", (255, 0, 0)), ("Yeşil", (0, 255, 0)), ("Mavi", (0, 0, 255)),
              ("Beyaz", (255, 255, 255)), ("Mor", (160, 0, 255)), ("Turkuaz", (0, 255, 255)),
              ("Sarı", (255, 255, 0)), ("Turuncu", (255, 128, 0)), ("Pembe", (255, 0, 160))]
DPILED_MODES = [(1, "Sabit ışık"), (2, "Yanıp sönme")]


def log(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + chr(10))
    except Exception:
        pass


DPI_TABLE = cp.DPI_TABLE
DPI_REVERSE = cp.DPI_REVERSE


def dpi_encode(dpi):
    """CrossFire kuralı: <=4000 doğrudan, üstü DPIex=0x11 ve tablo[dpi/2]."""
    if dpi <= 4000:
        return DPI_TABLE[dpi], 0x00
    return DPI_TABLE[dpi // 2], 0x11


def dpi_decode(x, ex):
    base = DPI_REVERSE.get(x)
    if base is None:
        return None
    return base * 2 if ex == 0x11 else base


# ---- vendor uygulaması çalışıyor mu --------------------------------------
class _PE32(ctypes.Structure):
    _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)), ("th32ModuleID", w.DWORD),
                ("cntThreads", w.DWORD), ("th32ParentProcessID", w.DWORD), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", w.DWORD), ("szExeFile", ctypes.c_char * 260)]


_k32 = ctypes.windll.kernel32
_k32.CreateToolhelp32Snapshot.restype = w.HANDLE


def vendor_running():
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


# ---- fare durumu -----------------------------------------------------------
class Mouse:
    def __init__(self):
        self.lock = threading.RLock()
        self.path = None
        self.flash = None
        self.battery = None        # (seviye, şarj)
        self.long_range = None
        self.status = "nodevice"   # nodevice | paused | asleep | ok
        self._cfg_time = 0
        self._paths = []
        self._paths_time = 0

    # -- okuma --
    def _pick_path(self):
        """HID numaralandirma pahali (~100-300 ms): 30 sn onbellekle, hata olursa hemen tazele."""
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
                    log("pil hata: %r" % e)
            if got is None:
                self.status = "asleep"
                self._paths_time = 0      # bir sonraki turda yollari yeniden tara
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

    # -- yazma --
    def _can_write(self):
        return self.status == "ok" and self.path is not None and not vendor_running_cached()

    def set_byte(self, addr, val):
        with self.lock:
            if not self._can_write():
                return False
            ok = cp.write_byte(self.path, addr, val)
            if ok:
                self.flash[addr], self.flash[addr + 1] = val & 0xFF, (0x55 - val) & 0xFF
            log("yaz 0x%02X=%d -> %s" % (addr, val, ok))
            return ok

    def set_group(self, addr, vals):
        """Çok baytlı alan: değerler + 0x55-toplam sağlaması."""
        with self.lock:
            if not self._can_write():
                return False
            data = bytes(vals) + bytes([(0x55 - sum(vals)) & 0xFF])
            ok = cp.write_flash(self.path, addr, data) and cp.read_flash(self.path, addr, len(data)) == data
            if ok:
                self.flash[addr:addr + len(data)] = data
            log("yaz 0x%02X=%s -> %s" % (addr, data.hex(" "), ok))
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
            log("uzun menzil=%s -> %s" % (on, ok))
            return ok


# ---- simge -----------------------------------------------------------------
def make_icon(level, charging, paused=False):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if level is None:
        col, txt, fg = (110, 110, 110), ("II" if paused else "--"), (235, 235, 235)
    else:
        col = (60, 170, 60) if level > 33 else (235, 150, 30) if level > 15 else (220, 50, 50)
        txt, fg = str(level), (255, 255, 255)
    d.rounded_rectangle((0, 0, 63, 63), radius=12, fill=col)
    if charging:
        d.rounded_rectangle((0, 0, 63, 63), radius=12, outline=(255, 225, 0), width=5)
    size = 46 if len(txt) <= 2 else 34
    try:
        font = ImageFont.truetype("arialbd.ttf", size)
    except Exception:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((64 - tw) / 2 - bbox[0], (64 - th) / 2 - bbox[1] - 2), txt, font=font, fill=fg)
    if charging:
        d.polygon([(52, 38), (46, 52), (51, 52), (49, 62), (58, 48), (53, 48)], fill=(255, 225, 0))
    return img


# ---- uygulama ---------------------------------------------------------------
def single_instance():
    """Ikinci kopya acilirsa sessizce cik (tepside iki simge olmasin)."""
    _k32.CreateMutexW(None, False, "ClawTray_TekOrnek")
    return _k32.GetLastError() != 183   # ERROR_ALREADY_EXISTS


def main():
    if "--durum" not in sys.argv and not single_instance():
        return
    m = Mouse()
    if "--durum" in sys.argv:
        m.poll(force_config=True)
        print("durum:", m.status, "| pil:", m.battery, "| uzun menzil:", m.long_range)
        if m.flash:
            n = m.byte(A_MAXDPI) or 0
            print("rapor hızı kodu:", m.byte(A_RATE), "| kademe:", n, "| aktif:", m.byte(A_CURDPI),
                  "| DPI:", [m.dpi(i) for i in range(n)])
            print("debounce:", m.byte(A_DEBOUNCE), "| motion:", m.byte(A_MOTION), "| açı:", m.byte(A_ANGLE),
                  "| ripple:", m.byte(A_RIPPLE), "| perf:", m.byte(A_PERF_EN), m.byte(A_PERF_TIME))
            print("ışık:", m.led(), "| kapanma:", m.byte(A_LEDOFF), "| hareketle kapat:", m.byte(A_MOVEOFF))
            print("DPI ışığı: mod", m.byte(A_DL_MODE), "etkin", m.byte(A_DL_EN))
        return

    import pystray
    from pystray import Menu, MenuItem as Item

    icon = pystray.Icon("ClawTray", make_icon(None, False), "Claw Fare")
    st = {"charging": None, "warned": set()}

    def notify(msg):
        try:
            icon.notify(msg, "Claw Fare")
        except Exception as e:
            log("bildirim hata: %r" % e)

    def title_text():
        if m.status == "paused":
            return "Claw Fare: CrossFire açık - duraklatıldı"
        if m.status == "asleep":
            return "Claw Fare: uykuda (hareket ettirin)"
        if m.status == "ok" and m.battery:
            lvl, chg = m.battery
            n = m.byte(A_CURDPI)
            dpi = m.dpi(n) if n is not None else None
            t = "Claw Fare: %%%d" % lvl + (" (şarj oluyor)" if chg else "")
            return t + (" - %d DPI" % dpi if dpi else "")
        return "Claw Fare"

    last = {"icon": None, "menu": None, "title": None, "visible": None}

    def redraw():
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
        t = title_text()
        if t != last["title"]:
            icon.title = t
            last["title"] = t
        msig = (m.status, bytes(m.flash) if m.flash else None, m.long_range)
        if msig != last["menu"]:
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
            notify(("Şarj başladı (%%%d)" if chg else "Şarj kablosu çıktı (%%%d)") % lvl)
            st["warned"].discard("full")
        if chg and lvl >= 100 and "full" not in st["warned"]:
            notify("Pil doldu (%100), kabloyu çıkarabilirsiniz")
            st["warned"].add("full")
        if not chg:
            for th in (20, 10):
                key = "low%d" % th
                if lvl <= th and key not in st["warned"]:
                    notify("Pil %%%d - şarj edin" % lvl)
                    st["warned"].add(key)
                elif lvl > th + 5:
                    st["warned"].discard(key)
        st["charging"] = chg

    def refresh(force=False):
        try:
            m.poll(force_config=force)
            battery_notifications()
        except Exception as e:
            log("yenileme hata: %r" % e)
        redraw()

    def loop():
        while True:
            refresh()
            time.sleep(DEVICE_POLL if m.status == "nodevice" else BATTERY_INTERVAL)

    # -- menü yardımcıları --
    def ready(_item=None):
        return m.status == "ok" and m.flash is not None

    def act(fn):
        """Yazma eylemi sarmalayıcı: başarısızsa bildirir, sonra menüyü tazeler."""
        def work():
            ok = False
            try:
                ok = fn()
            except Exception as e:
                log("eylem hata: %r" % e)
            if not ok:
                notify("Ayar yazılamadı - fare uykuda ya da CrossFire açık olabilir")
            redraw()

        def run(_icon, _item):
            threading.Thread(target=work, daemon=True).start()
        return run

    def radio(text, getter, value, setter):
        return Item(text, act(lambda: setter(value)), checked=lambda _i: getter() == value, radio=True, enabled=ready)

    def toggle(text, addr):
        return Item(text, act(lambda: m.set_byte(addr, 0 if m.byte(addr) else 1)),
                    checked=lambda _i: bool(m.byte(addr)), enabled=ready)

    def stage_menu(i):
        def visible(_i):
            return (m.byte(A_MAXDPI) or 0) > i
        items = [radio("%d DPI" % d, lambda i=i: m.dpi(i), d, lambda v, i=i: m.set_dpi(i, v)) for d in DPI_CHOICES]
        return Item(lambda _i, i=i: "Kademe %d değeri (%s)" % (i + 1, m.dpi(i) or "?"), Menu(*items),
                    visible=visible, enabled=ready)

    def active_stage_items():
        out = []
        for i in range(6):
            out.append(Item(lambda _i, i=i: "Kademe %d: %s DPI" % (i + 1, m.dpi(i) or "?"),
                            act(lambda i=i: m.set_byte(A_CURDPI, i)),
                            checked=lambda _i, i=i: m.byte(A_CURDPI) == i, radio=True,
                            visible=lambda _i, i=i: (m.byte(A_MAXDPI) or 0) > i, enabled=ready))
        return out

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
        if not led or not led["en"]:
            return 0
        return led["mode"]

    def set_dpiled(code):
        if code == 0:
            return m.set_byte(A_DL_EN, 0)
        return m.set_byte(A_DL_MODE, code) and m.set_byte(A_DL_EN, 1)

    def dpiled_state():
        return (m.byte(A_DL_MODE) or 0) if m.byte(A_DL_EN) else 0

    def preset(dpi, label):
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
                notify("%s ön ayarı uygulandı (%d DPI)" % (label, dpi))
            return ok
        return run

    dpi_menu = Menu(
        Item("Aktif kademe", Menu(*active_stage_items()), enabled=ready),
        Menu.SEPARATOR,
        *[stage_menu(i) for i in range(6)],
        Menu.SEPARATOR,
        Item("Kademe sayısı", Menu(*[radio(str(n), lambda: m.byte(A_MAXDPI), n, lambda v: m.set_byte(A_MAXDPI, v))
                                     for n in range(1, 7)]), enabled=ready),
    )
    sensor_menu = Menu(
        toggle("Motion sync", A_MOTION),
        toggle("Açı düzeltme (angle snapping)", A_ANGLE),
        toggle("Ripple kontrolü", A_RIPPLE),
        Menu.SEPARATOR,
        Item("Maksimum performans", Menu(
            radio("Kapalı", perf_state, 0, set_perf),
            *[radio(t, perf_state, c, set_perf) for c, t in PERF_TIMES]), enabled=ready),
    )
    light_menu = Menu(
        Item("Mod", Menu(radio("Kapalı", led_mode_state, 0, set_led_mode),
                         *[radio(t, led_mode_state, c, set_led_mode) for c, t in LED_MODES]), enabled=ready),
        Item("Renk", Menu(*[radio(n, lambda: (m.led() or {}).get("rgb"), rgb, lambda v: m.set_led(rgb=v))
                            for n, rgb in LED_COLORS]), enabled=ready),
        Item("Parlaklık", Menu(*[radio(str(n), lambda: (m.led() or {}).get("bright"), n - 1,
                                       lambda v: m.set_led(bright=v)) for n in range(1, 11)]), enabled=ready),
        Item("Hız", Menu(*[radio(str(n), lambda: (m.led() or {}).get("speed"), n - 1,
                                 lambda v: m.set_led(speed=v)) for n in range(1, 11)]), enabled=ready),
        Menu.SEPARATOR,
        toggle("Hareket ederken ışığı kapat", A_MOVEOFF),
        Item("Hareketsiz kalınca kapanma süresi", Menu(
            *[radio(t, lambda: m.byte(A_LEDOFF), c, lambda v: m.set_byte(A_LEDOFF, v)) for c, t in LEDOFF_TIMES]),
            enabled=ready),
        Menu.SEPARATOR,
        Item("DPI gösterge ışığı", Menu(radio("Kapalı", dpiled_state, 0, set_dpiled),
                                        *[radio(t, dpiled_state, c, set_dpiled) for c, t in DPILED_MODES]),
             enabled=ready),
    )
    icon.menu = Menu(
        Item(lambda _i: title_text(), None, enabled=False),
        Menu.SEPARATOR,
        Item("Ön ayarlar", Menu(Item("CS2 (800 DPI)", act(preset(800, "CS2")), enabled=ready),
                                Item("Masaüstü (1600 DPI)", act(preset(1600, "Masaüstü")), enabled=ready)),
             enabled=ready),
        Item("DPI", dpi_menu, enabled=ready),
        Item("Rapor hızı", Menu(*[radio(t, lambda: m.byte(A_RATE), c, lambda v: m.set_byte(A_RATE, v))
                                  for c, t in RATES]), enabled=ready),
        Item("Debounce", Menu(*[radio("%d ms" % d, lambda: m.byte(A_DEBOUNCE), d,
                                      lambda v: m.set_byte(A_DEBOUNCE, v)) for d in DEBOUNCES]), enabled=ready),
        Item("Sensör", sensor_menu, enabled=ready),
        Item("Işık", light_menu, enabled=ready),
        Item("Uzun menzil modu", act(lambda: m.set_long_range(not m.long_range)),
             checked=lambda _i: bool(m.long_range), enabled=ready),
        Menu.SEPARATOR,
        Item("Şimdi yenile", lambda _ic, _it: threading.Thread(target=refresh, args=(True,), daemon=True).start()),
        Item("Çıkış", lambda ic, _it: ic.stop()),
    )

    def setup(ic):
        ic.visible = bool(cp.device_paths())
        threading.Thread(target=loop, daemon=True).start()

    log("claw_tray başladı")
    icon.run(setup=setup)


if __name__ == "__main__":
    main()
