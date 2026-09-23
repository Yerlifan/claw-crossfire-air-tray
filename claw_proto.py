# -*- coding: utf-8 -*-
"""Claw CrossFire AIR V1 - HID protokol katmanı (saf hidapi, üretici DLL'i gerekmez).

Fare / alıcı, VID 0x3554 üzerinde usage page 0xFF02 olan HID koleksiyonuyla konuşur.
Paket (17 bayt, çıkış raporu -> giriş raporu):
  [0]=0x08 rapor kimliği  [1]=komut  [2]=durum  [3..4]=adres (big-endian)
  [5]=uzunluk (<=10)      [6..15]=veri           [16]=0x55 - toplam(0..15)
Komutlar: 0x03 çevrimiçi, 0x04 pil, 0x07 flash yaz, 0x08 flash oku, 0x12 sürüm,
          0x16 / 0x17 uzun menzil yaz / oku.
Flash'ta her tek baytlık ayar (değer, 0x55-değer) çifti; çok baytlı gruplar 0x55-toplam ile biter.
"""
import threading
import time

VID, USAGE_PAGE = 0x3554, 0xFF02
PID_WIRED, PID_DONGLE = 0xF5A7, 0xF512
CMD_ONLINE, CMD_BATTERY, CMD_WRITE, CMD_READ = 0x03, 0x04, 0x07, 0x08
CMD_VERSION, CMD_LR_SET, CMD_LR_GET = 0x12, 0x16, 0x17
REPORT_ID = 0x08
TIMEOUT_MS = 800

# PixArt PAW3325 DPI kod tablosu (üreticinin driver_sensor.h dosyasından; >4000 DPI için ex=0x11 ve tablo[dpi/2]).
DPI_TABLE = {
    200: 0x04, 300: 0x06, 400: 0x08, 500: 0x0B, 600: 0x0D, 700: 0x0F, 800: 0x12,
    900: 0x14, 1000: 0x16, 1100: 0x19, 1200: 0x1B, 1300: 0x1D, 1400: 0x20, 1500: 0x22,
    1600: 0x24, 1700: 0x27, 1800: 0x29, 1900: 0x2B, 2000: 0x2E, 2100: 0x30, 2200: 0x32,
    2300: 0x34, 2400: 0x37, 2500: 0x39, 2600: 0x3B, 2700: 0x3E, 2800: 0x40, 2900: 0x42,
    3000: 0x45, 3100: 0x47, 3200: 0x49, 3300: 0x4C, 3400: 0x4E, 3500: 0x50, 3600: 0x53,
    3700: 0x55, 3800: 0x57, 3900: 0x5A, 4000: 0x5C, 4100: 0x5E, 4200: 0x61, 4300: 0x63,
    4400: 0x65, 4500: 0x68, 4600: 0x6A, 4700: 0x6C, 4800: 0x6F, 4900: 0x71, 5000: 0x73,
}
DPI_REVERSE = {v: k for k, v in DPI_TABLE.items()}

_lock = threading.RLock()


def device_paths():
    """0xFF02 koleksiyonları; kablolu bağlantı (F5A7) önce, sonra alıcı (F512)."""
    import hid
    devs = [dv for dv in hid.enumerate(VID) if dv["usage_page"] == USAGE_PAGE]
    devs.sort(key=lambda dv: 0 if dv["product_id"] == PID_WIRED else 1)
    return [dv["path"] for dv in devs]


def packet(cmd, addr=0, length=0, data=b""):
    p = bytearray(17)
    p[0], p[1] = REPORT_ID, cmd
    p[3], p[4], p[5] = (addr >> 8) & 0xFF, addr & 0xFF, length
    p[6:6 + len(data)] = data
    p[16] = (0x55 - sum(p[:16])) & 0xFF
    return bytes(p)


def checksum_ok(r):
    return len(r) >= 17 and r[16] == (0x55 - sum(r[:16])) & 0xFF


def xfer(path, pkt, tries=3):
    """Paketi gönderir, aynı komut+adres ile gelen yanıtı döndürür; yoksa None.
    (Uzunluk karşılaştırılmaz: pil/sürüm isteklerinde 0, yanıtta 2 gelir.)"""
    import hid
    with _lock:
        for _ in range(tries):
            d = hid.device()
            try:
                d.open_path(path)
                d.write(pkt)
                t0 = time.time()
                while (time.time() - t0) * 1000 < TIMEOUT_MS:
                    r = bytes(d.read(64, TIMEOUT_MS))
                    if not r:
                        break
                    if r[0] == REPORT_ID and r[1] == pkt[1] and r[3:5] == pkt[3:5] and checksum_ok(r):
                        return r[:17]
            except (OSError, ValueError):
                pass
            finally:
                try:
                    d.close()
                except Exception:
                    pass
    return None


def is_online(path):
    r = xfer(path, packet(CMD_ONLINE))
    return bool(r and r[6])


def battery(path):
    """(seviye %, şarj oluyor mu) ya da None. Fare uykudaysa seviye 0 döner."""
    r = xfer(path, packet(CMD_BATTERY))
    if r is None:
        return None
    return r[6], bool(r[7])


def version(path):
    r = xfer(path, packet(CMD_VERSION))
    return r[6] if r else None


def read_flash(path, addr, n):
    buf = bytearray()
    while n > 0:
        k = min(10, n)
        r = xfer(path, packet(CMD_READ, addr, k))
        if r is None:
            return None
        buf += r[6:6 + k]
        addr += k
        n -= k
    return bytes(buf)


def write_flash(path, addr, data):
    """Ham yazma (<=10 bayt). Başarı: yanıt gelir ve durum baytı 0'dır."""
    assert 0 < len(data) <= 10
    r = xfer(path, packet(CMD_WRITE, addr, len(data), bytes(data)))
    return bool(r is not None and r[2] == 0)


def write_byte(path, addr, val):
    """Tek baytlık ayar: (değer, 0x55-değer) çiftini yazar, geri okuyup doğrular."""
    pair = bytes([val & 0xFF, (0x55 - val) & 0xFF])
    if not write_flash(path, addr, pair):
        return False
    return read_flash(path, addr, 2) == pair


def get_long_range(path):
    r = xfer(path, packet(CMD_LR_GET))
    return bool(r[6]) if r else None


def set_long_range(path, on):
    v = 1 if on else 0
    r = xfer(path, packet(CMD_LR_SET, 0, 0x0A, bytes([v])))
    return bool(r is not None and r[6] == v)
