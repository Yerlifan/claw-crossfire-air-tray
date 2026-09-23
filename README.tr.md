# Claw CrossFire AIR: sistem tepsisi denetimi

🇹🇷 **Türkçe** · 🇬🇧 [English](README.md) · 🇪🇸 [Español](README.es.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇷🇺 [Русский](README.ru.md) · 🇨🇳 [中文](README.zh.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇸🇦 [العربية](README.ar.md)

**Claw CrossFire AIR V1** kablosuz fare için küçük bir sistem tepsisi uygulaması. Üreticinin yazılımına da DLL'ine de ihtiyaç duymaz; fareyle doğrudan USB HID üzerinden konuşur. Windows için, Linux desteği beta.

![Tepsi menüsü](docs/screenshot.png)

## Özellikler

| | |
|---|---|
| **Pil** | Tepside büyük rakamla yüzde, şarjda sarı çerçeve. Şarj başlayınca ve bitince, pil dolunca, %20 ve %10'a düşünce bildirim. Fare uykudayken simge `II` gösterir, fare takılı değilken gizlenir. |
| **Tüm ayarlar sağ tık menüsünde** | DPI kademeleri (değerler, aktif kademe, kademe sayısı), rapor hızı, debounce, motion sync, açı düzeltme, ripple kontrolü, maksimum performans, ışık modu, renk, parlaklık, hız, hareket ederken ışığı kapatma, kapanma süresi, DPI gösterge ışığı, uzun menzil modu. Yazılan her ayar fareden geri okunarak doğrulanır. |
| **Beş düzenlenebilir ön ayar** | Oyun, Masaüstü, Hassas, Pil Tasarrufu, Sunum. Tek tıkla uygula, farenin o anki ayarlarını yuvaya kaydet, yeniden adlandır, varsayılana döndür. `config.json` içinde saklanır. |
| **Yardım** | Yardım alt menüsü her ayarı listeler; birine tıklayınca kısa açıklaması bildirim olarak çıkar. "Rehberi Aç" tüm açıklamaları kaydırılabilir bir pencerede gösterir. |
| **On dil** | Türkçe, English, Español, Français, Deutsch, Русский, 中文, 日本語, 한국어, العربية. Sistem dilini izler, menüden değiştirilebilir; seçim hatırlanır. |
| **Hafif** | Tek bir tepsi simgesi; servis yok, sürücü yok, kendi klasörü ve `config.json` dışında hiçbir yere yazmaz. İsterseniz Windows ile başlar. |

> Bu araç üreticiyle ilişkili değildir. Protokol, üretici yazılımının fareye gönderdikleri izlenerek tersine mühendislikle çıkarılmıştır ve yalnızca **CrossFire AIR V1** (PixArt PAW3325, firmware v2.0, 2.4 GHz alıcı) ile test edilmiştir. Kullanım kendi sorumluluğunuzdadır.

## Kurulum

### Seçenek A: hazır program (Python gerekmez)

1. [Releases](https://github.com/Yerlifan/claw-crossfire-air-tray/releases) sayfasından `ClawTray_<sürüm>_win64.zip` dosyasını indirip istediğiniz bir klasöre açın (ör. `C:\Users\<siz>\ClawTray`).
2. `ClawTray.exe`'yi çalıştırın. Simge sistem tepsisinde belirir (`^` altında olabilir).
3. İsteğe bağlı, Başlat menüsü, masaüstü ve Windows ile başlatma kısayolları:
   ```powershell
   powershell -ExecutionPolicy Bypass -File kurulum.ps1
   ```

Windows SmartScreen ilk açılışta imzasız program uyarısı verebilir; *Ek bilgi, Yine de çalıştır* deyin ya da B seçeneğini kullanın.

### Seçenek B: kaynak koddan

Gereksinimler: Windows 10/11 (ya da Linux, bkz. C seçeneği), Python 3.10+.

```powershell
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
pip install -r requirements.txt
pythonw claw_tray.py
```

`kurulum.ps1` burada da çalışır (yanında `ClawTray.exe` yoksa `pythonw` kullanır). Kaldırmak için `kurulum.ps1 -Kaldir` çalıştırıp klasörü silin.

Komut satırı: `--durum` mevcut durumu yazar, `--lang tr` dili zorlar, `--guide` rehber penceresini açar.

### Seçenek C: Linux (beta, gerçek donanımda henüz test edilmedi)

Farenin kendisi Linux'ta sürücü istemez; bu araç yalnızca tepsideki pil ve ayar arayüzünü ekler. Protokol katmanı aynıdır, ancak Linux taşıması yalnızca fare takılı olmayan bir sanal makinede doğrulanabildi. Gerçek donanımdan geri bildirim çok değerli.

```bash
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
./linux/kurulum.sh        # udev kuralı (sudo), pip paketleri, .desktop + otomatik başlatma, sonra başlatır
```

Debian/Ubuntu'da tepsi arka ucu ve rehber penceresi için: `sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 python3-tk`; GNOME'da ayrıca *AppIndicator* eklentisini açın. Kaldırmak için `./linux/kurulum.sh -u`. Ayarlar `~/.config/clawtray/` altında.

## Bilinmesi gerekenler

- **CrossFire yazılımıyla aynı anda çalışmaz.** İkisi aynı anda fareyle konuşursa CrossFire çöker (fareye bir şey olmaz); bu yüzden CrossFire açıkken araç kendini duraklatır (simgede `!`). CrossFire'ı kaldırabilirsiniz; bu araç ona bağımlı değildir.
- Fare uykudayken (yaklaşık bir dakika hareketsiz) ayar yazılamaz; simge `II` gösterir, hareket ettirince kendiliğinden düzelir.
- Bir şey ters giderse üreticinin yazılımındaki *Restore / Varsayılana Dön* fabrika ayarına döndürür.
- Makro ve tuş atama bilerek kapsam dışıdır.

## Nasıl çalışıyor

Fare (ya da alıcı) VID `0x3554` altında, usage page `0xFF02` olan bir HID koleksiyonu açar. Her komut 17 baytlık bir çıkış raporudur, yanıt aynı biçimde giriş raporu olarak gelir:

```
[0]  = 0x08 rapor kimliği   [1]     = komut          [2]  = durum
[3]  = adres üst bayt       [4]     = adres alt bayt  [5]  = uzunluk (en çok 10)
[6..15] = veri              [16]    = sağlama, sağlama = (0x55 - toplam(bayt 0..15)) & 0xFF
```

| Komut | İşlev |
|---|---|
| `0x03` | Fare çevrimiçi mi |
| `0x04` | Pil: `[6]` seviye %, `[7]` şarj oluyor |
| `0x07` / `0x08` | Ayar flash'ına yaz / oku |
| `0x12` | Sürüm |
| `0x16` / `0x17` | Uzun menzil modu yaz / oku |

Ayar flash'ında her tek baytlık alan `değer, sağlama` çifti olarak saklanır, `sağlama = (0x55 - değer) & 0xFF`; çok baytlı gruplar `sağlama = (0x55 - toplam) & 0xFF` ile biter:

| Adres | Alan |
|---|---|
| `0x00` | Rapor hızı (1 = 1000 Hz, 2 = 500, 4 = 250, 8 = 125) |
| `0x02` / `0x04` | DPI kademe sayısı / aktif kademe |
| `0x0C + 4i` | Kademe i DPI: `x, y, ex, sağlama`; DPI kodu PAW3325 tablosundan, 4000 DPI üstü için `ex = 0x11` ve tablo[DPI/2] |
| `0x2C + 4i` | Kademe i rengi `r, g, b, sağlama` |
| `0x4C` … `0x52` | DPI gösterge ışığı: mod, parlaklık, hız, etkin |
| `0xA0` … `0xA7` | Işık şeridi: mod, r, g, b, hız, parlaklık, sağlama; `0xA7` etkin |
| `0xA9` | Debounce (ms) |
| `0xAB` / `0xAF` / `0xB1` | Motion sync / açı düzeltme / ripple kontrolü |
| `0xAD` | Hareketsizlikte ışık kapanma süresi (×10 s) |
| `0xB3` | Hareket ederken ışığı kapat |
| `0xB5` / `0xB7` | Maksimum performans etkin / süresi (×10 s) |

Alan adları üreticinin yazılımıyla birlikte gelen hata ayıklama sembollerinden (`MouseConfig`, `LedBar`, `DPILed`, `DPIConfig`, `BatteryStatus`) alınmıştır. `claw_proto.py` bu katmanın tamamıdır ve tek başına da kullanılabilir.

## Dosyalar

| Dosya | |
|---|---|
| `claw_tray.py` | Tepsi uygulaması, menü, ön ayarlar, yardım, rehber penceresi |
| `claw_proto.py` | Protokol katmanı (hidapi) ve PAW3325 DPI tablosu |
| `claw_lang.py` | On dildeki tüm arayüz metinleri |
| `kurulum.ps1` | Windows kısayollarını oluşturur / kaldırır |
| `linux/kurulum.sh`, `linux/70_clawcrossfire.rules` | Linux kurulum betiği ve udev kuralı |
| `claw.ico` / `claw.png` | Uygulama simgesi (Windows / Linux) |
| `build.ps1` | PyInstaller ile `ClawTray.exe` ve sürüm zip'ini üretir |

## Lisans

MIT, bkz. [LICENSE](LICENSE).
