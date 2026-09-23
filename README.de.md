# Claw CrossFire AIR: Steuerung aus dem Infobereich

🇹🇷 [Türkçe](README.tr.md) · 🇬🇧 [English](README.md) · 🇪🇸 [Español](README.es.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 **Deutsch** · 🇷🇺 [Русский](README.ru.md) · 🇨🇳 [中文](README.zh.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇸🇦 [العربية](README.ar.md)

Eine kleine Anwendung im Infobereich für die kabellose Maus **Claw CrossFire AIR V1**. Sie braucht weder die Herstellersoftware noch deren DLL: sie spricht direkt über USB HID mit der Maus. Windows, Linux Unterstützung in der Beta.

## Funktionen

| | |
|---|---|
| **Akku** | Prozentzahl groß im Infobereich, gelber Rahmen beim Laden. Benachrichtigungen bei Beginn und Ende des Ladens, bei vollem Akku sowie bei 20% und 10%. Das Symbol zeigt `II`, während die Maus schläft, und verschwindet, wenn keine Maus verbunden ist. |
| **Alle Einstellungen im Kontextmenü** | DPI Stufen (Werte, aktive Stufe, Anzahl), Abfragerate, Entprellung, Motion Sync, Winkelkorrektur, Ripple Kontrolle, maximale Leistung, Beleuchtungsmodus, Farbe, Helligkeit, Geschwindigkeit, Licht bei Bewegung aus, Abschaltverzögerung, DPI Anzeigelicht, Langstreckenmodus. Jeder Schreibvorgang wird von der Maus zurückgelesen und geprüft. |
| **Fünf bearbeitbare Voreinstellungen** | Spielen, Desktop, Präzision, Energiesparen, Präsentation. Mit einem Klick anwenden, die aktuellen Mauseinstellungen in einen Speicherplatz übernehmen, umbenennen, zurücksetzen. Gespeichert in `config.json`. |
| **Hilfe** | Das Untermenü Hilfe listet jede Einstellung; ein Klick zeigt eine kurze Erklärung als Benachrichtigung. „Anleitung öffnen“ zeigt alle Erklärungen in einem scrollbaren Fenster. |
| **Zehn Sprachen** | Türkçe, English, Español, Français, Deutsch, Русский, 中文, 日本語, 한국어, العربية. Folgt der Systemsprache und lässt sich im Menü umschalten; die Wahl wird gespeichert. |
| **Leichtgewichtig** | Ein Symbol, kein Dienst, kein Treiber, außer `config.json` wird nichts außerhalb des eigenen Ordners geschrieben. Startet auf Wunsch mit Windows. |

> Nicht mit dem Hersteller verbunden. Das Protokoll wurde durch Beobachten der Herstellersoftware per Reverse Engineering ermittelt und nur mit der **CrossFire AIR V1** (PixArt PAW3325, Firmware v2.0, 2,4 GHz Empfänger) getestet. Benutzung auf eigene Gefahr.

## Installation

### Option A: fertige ausführbare Datei (kein Python nötig)

1. `ClawTray_<Version>_win64.zip` von der Seite [Releases](https://github.com/Yerlifan/claw-crossfire-air-tray/releases) laden und in einen beliebigen Ordner entpacken.
2. `ClawTray.exe` starten. Das Symbol erscheint im Infobereich (eventuell unter dem Pfeil `^`).
3. Optional, Verknüpfungen im Startmenü, auf dem Desktop und im Autostart:
   ```powershell
   powershell -ExecutionPolicy Bypass -File kurulum.ps1
   ```

Windows SmartScreen kann beim ersten Start warnen, weil die Datei nicht signiert ist; wählen Sie *Weitere Informationen, Trotzdem ausführen* oder nutzen Sie Option B.

### Option B: aus dem Quellcode

Voraussetzungen: Windows 10/11 (oder Linux, siehe Option C), Python 3.10 oder neuer.

```powershell
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
pip install -r requirements.txt
pythonw claw_tray.py
```

Deinstallation: `kurulum.ps1 -Kaldir`, danach den Ordner löschen. Kommandozeile: `--status` zeigt den Zustand, `--lang de` erzwingt die Sprache, `--guide` öffnet die Anleitung.

### Option C: Linux (Beta, noch nicht auf echter Hardware getestet)

Die Maus selbst braucht unter Linux keinen Treiber; diese Anwendung ergänzt nur die Akku und Einstellungsoberfläche. Die Linux Portierung konnte nur in einer virtuellen Maschine ohne angeschlossene Maus geprüft werden; Rückmeldungen von echter Hardware sind willkommen.

```bash
./linux/kurulum.sh        # udev Regel (sudo), pip Pakete, .desktop + Autostart
```

Debian/Ubuntu Pakete: `sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 python3-tk`; unter GNOME zusätzlich die Erweiterung *AppIndicator* aktivieren. Deinstallation: `./linux/kurulum.sh -u`.

## Gut zu wissen

- **Läuft nicht gleichzeitig mit der CrossFire Software.** Sprechen beide zugleich mit der Maus, stürzt CrossFire ab (die Maus bleibt unberührt); die Anwendung pausiert deshalb, solange CrossFire läuft (Symbol `!`). CrossFire kann deinstalliert werden; die Anwendung hängt nicht davon ab.
- Im Ruhezustand der Maus (etwa eine Minute ohne Bewegung) lassen sich keine Einstellungen schreiben: das Symbol zeigt `II` und erholt sich, sobald die Maus bewegt wird.
- Falls etwas schiefgeht, setzt *Restore* in der Herstellersoftware die Maus auf Werkseinstellungen zurück.
- Makros und Tastenbelegung sind bewusst nicht enthalten.

## Protokolldetails

Paketformat, Befehlstabelle und die Karte des Einstellungsspeichers sind im [englischen README](README.md#how-it-works) dokumentiert. `claw_proto.py` ist die gesamte Protokollschicht und lässt sich eigenständig verwenden.

## Lizenz

MIT, siehe [LICENSE](LICENSE).
