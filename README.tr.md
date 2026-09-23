# Claw CrossFire AIR — sistem tepsisi denetimi

🇹🇷 Türkçe · 🇬🇧 **[English](README.md)**

Claw CrossFire AIR V1 kablosuz fare için üreticinin yazılımına da DLL'ine de ihtiyaç duymayan, hafif bir sistem tepsisi aracı (Windows; Linux beta).

- **Pil yüzdesi** tepside büyük rakamla; şarj başlayınca / bitince, pil %20 ve %10'a düşünce Windows bildirimi
- **Tüm ayarlar sağ tık menüsünde:** DPI kademeleri, rapor hızı, debounce, motion sync, açı düzeltme, ripple kontrolü, maksimum performans, ışık modu / renk / parlaklık / hız, uzun menzil modu
- **Ön ayarlar:** tek tıkla "CS2 (800 DPI)" veya "Masaüstü (1600 DPI)"
- Fareyle **doğrudan USB üzerinden** konuşur — `HIDUsb.dll` ya da CrossFire yazılımı gerekmez
- Menü **Türkçe veya İngilizce** — Windows görüntü dilini izler, menüden değiştirilebilir
- Fare takılı değilken simge gizlenir; Windows ile birlikte başlar

> Bu araç üreticiyle ilişkili değildir. Protokol, üretici yazılımının fareye gönderdikleri izlenerek tersine mühendislikle çıkarılmıştır ve yalnızca **CrossFire AIR V1** (PixArt PAW3325, firmware v2.0, 2.4 GHz alıcı) ile test edilmiştir. Kullanım kendi sorumluluğunuzdadır.

## Kurulum

### Seçenek A — hazır program (Python gerekmez)

1. [Releases](https://github.com/Yerlifan/claw-crossfire-air-tray/releases) sayfasından `ClawTray-<sürüm>-win64.zip` dosyasını indirip istediğiniz bir klasöre açın (ör. `C:\Users\<siz>\ClawTray`).
2. `ClawTray.exe`'yi çalıştırın. Simge sistem tepsisinde belirir (`^` altında olabilir).
3. İsteğe bağlı — Başlat menüsü, masaüstü ve Windows ile başlatma kısayolları:
   ```powershell
   powershell -ExecutionPolicy Bypass -File kurulum.ps1
   ```

Windows SmartScreen ilk açılışta imzasız program uyarısı verebilir; *Ek bilgi → Yine de çalıştır* deyin ya da B seçeneğini kullanın.

### Seçenek B — kaynak koddan

Gereksinimler: Windows 10/11 (ya da Linux, bkz. C seçeneği), Python 3.10+.

```powershell
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
pip install -r requirements.txt
pythonw claw_tray.py
```

`kurulum.ps1` burada da çalışır (yanında `ClawTray.exe` yoksa `pythonw` kullanır). Kaldırmak için `kurulum.ps1 -Kaldir` çalıştırıp klasörü silin; sisteme başka hiçbir şey yazılmaz.

Mevcut durumu terminalden görmek için: `python claw_tray.py --durum` (ya da `ClawTray.exe --durum`). Dili zorlamak için: `--lang tr` / `--lang en`.

### Seçenek C — Linux (beta, gerçek donanımda henüz test edilmedi)

Farenin kendisi Linux'ta sürücü istemez; bu araç yalnızca tepsideki pil/ayar arayüzünü ekler. Protokol katmanı aynıdır, ancak Linux taşımasını yalnızca fare takılı olmayan bir sanal makinede doğrulayabildim — gerçek donanımdan geri bildirim çok değerli.

```bash
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
./linux/kurulum.sh        # udev kuralı (sudo), pip paketleri, .desktop + otomatik başlatma, sonra başlatır
```

Debian/Ubuntu'da tepsi arka ucu için: `sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1`; GNOME'da ayrıca *AppIndicator* eklentisini açın. Kaldırmak için `./linux/kurulum.sh -u`. Ayarlar `~/.config/claw-tray/` altında.

## Bilinmesi gerekenler

- **CrossFire yazılımıyla aynı anda çalışmaz.** İkisi aynı anda fareyle konuşursa CrossFire çöker (fareye bir şey olmaz); bu yüzden CrossFire açıkken araç kendini duraklatır (simgede `II`). CrossFire'ı kaldırabilirsiniz; bu araç ona bağımlı değildir.
- Fare uykudayken (hareketsiz ~1 dk) ayar yazılamaz; simge gri `--` olur, hareket ettirince kendiliğinden düzelir.
- Yazılan her ayar fareden geri okunarak doğrulanır. Bir şey ters giderse üreticinin yazılımındaki **Restore / Varsayılana Dön** fabrika ayarına döndürür.
- Makro ve tuş atama bilerek kapsam dışıdır.

## Nasıl çalışıyor

Fare (ya da alıcı) VID `0x3554` altında, usage page `0xFF02` olan bir HID koleksiyonu açar. Her komut 17 baytlık bir çıkış raporudur, yanıt aynı biçimde giriş raporu olarak gelir:

```
[0]=0x08 rapor kimliği  [1]=komut  [2]=durum  [3..4]=adres (big-endian)
[5]=uzunluk (≤10)       [6..15]=veri           [16]=0x55 − toplam(0..15)
```

| Komut | İşlev |
|---|---|
| `0x03` | Fare çevrimiçi mi |
| `0x04` | Pil: `[6]` seviye %, `[7]` şarj oluyor |
| `0x07` / `0x08` | Ayar flash'ına yaz / oku |
| `0x12` | Sürüm |
| `0x16` / `0x17` | Uzun menzil modu yaz / oku |

Ayar flash'ında her tek baytlık alan `(değer, 0x55 − değer)` çifti olarak, çok baytlı gruplar sonunda `0x55 − toplam` ile saklanır:

| Adres | Alan |
|---|---|
| `0x00` | Rapor hızı (1 = 1000 Hz, 2 = 500, 4 = 250, 8 = 125) |
| `0x02` / `0x04` | DPI kademe sayısı / aktif kademe |
| `0x0C + 4i` | Kademe i DPI: `x, y, ex, sağlama` — DPI kodu PAW3325 tablosundan; > 4000 DPI için `ex = 0x11` ve tablo[DPI/2] |
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
| `claw_tray.py` | Tepsi uygulaması ve menü |
| `claw_proto.py` | Protokol katmanı (hidapi) ve PAW3325 DPI tablosu |
| `kurulum.ps1` | Kısayolları oluşturur / kaldırır |
| `claw.ico` / `claw.png` | Kısayol simgesi (Windows / Linux) |
| `linux/kurulum.sh`, `linux/70-claw-crossfire.rules` | Linux kurulum betiği ve udev kuralı |
| `build.ps1` | PyInstaller ile `ClawTray.exe` üretir |

## Lisans

MIT — bkz. [LICENSE](LICENSE).
