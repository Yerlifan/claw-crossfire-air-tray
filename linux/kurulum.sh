#!/usr/bin/env bash
# Claw CrossFire AIR tray: Linux installer / Linux kurulumu
#   ./linux/kurulum.sh          install: udev rule, Python deps, .desktop + autostart
#   ./linux/kurulum.sh -u       uninstall (keeps the folder)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$HERE/claw_tray.py"
ICON="$HERE/claw.png"
RULE_SRC="$HERE/linux/70_clawcrossfire.rules"
RULE_DST="/etc/udev/rules.d/70_clawcrossfire.rules"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
DESKTOP="$DESKTOP_DIR/clawtray.desktop"
AUTOSTART="$AUTOSTART_DIR/clawtray.desktop"

if [[ "${1:-}" == "-u" ]]; then
    rm -f "$DESKTOP" "$AUTOSTART"
    pkill -f "claw_tray.py" 2>/dev/null || true
    echo "Removed .desktop entries. To remove the udev rule: sudo rm $RULE_DST"
    echo "Kisayollar kaldirildi. udev kuralini kaldirmak icin: sudo rm $RULE_DST"
    exit 0
fi

command -v python3 >/dev/null || { echo "python3 not found / python3 bulunamadi"; exit 1; }

echo "== udev rule (needs sudo) / udev kurali (sudo ister) =="
if ! cmp -s "$RULE_SRC" "$RULE_DST" 2>/dev/null; then
    sudo install -m 644 "$RULE_SRC" "$RULE_DST"
    sudo udevadm control --reload
    sudo udevadm trigger
fi

echo "== Python packages / Python paketleri =="
python3 -m pip install --user -q -r "$HERE/requirements.txt" || {
    echo "pip failed. On Debian/Ubuntu try: sudo apt install python3-pip python3-dev libhidapi-hidraw0 libhidapi-dev"
    exit 1
}
python3 -c "import pystray" 2>/dev/null || {
    echo "pystray needs a tray backend. Debian/Ubuntu: sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1"
    echo "GNOME also needs the AppIndicator extension. / GNOME icin ayrica AppIndicator eklentisi gerekir."
}

echo "== .desktop entries / kisayollar =="
mkdir -p "$DESKTOP_DIR" "$AUTOSTART_DIR"
cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=Claw Mouse
Name[tr]=Claw Fare
Comment=Claw CrossFire AIR battery and settings in the tray
Comment[tr]=Claw CrossFire AIR pil ve ayarlari (tepsi)
Exec=python3 "$APP"
Icon=$ICON
Terminal=false
Categories=Utility;Settings;
EOF
cp "$DESKTOP" "$AUTOSTART"
echo "Installed: $DESKTOP (+ autostart)"

echo "== start / baslat =="
nohup python3 "$APP" >/dev/null 2>&1 &
echo "Running. Tray icon should appear; on GNOME enable the AppIndicator extension."
echo "Calisiyor. Simge tepside gorunmeli; GNOME'da AppIndicator eklentisini acin."
