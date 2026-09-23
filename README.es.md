# Claw CrossFire AIR: control desde la bandeja del sistema

🇹🇷 [Türkçe](README.tr.md) · 🇬🇧 [English](README.md) · 🇪🇸 **Español** · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇷🇺 [Русский](README.ru.md) · 🇨🇳 [中文](README.zh.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇸🇦 [العربية](README.ar.md)

Una pequeña aplicación de bandeja del sistema para el ratón inalámbrico **Claw CrossFire AIR V1**. No necesita el software del fabricante ni su DLL: habla con el ratón directamente por USB HID. Windows, con soporte para Linux en beta.

## Funciones

| | |
|---|---|
| **Batería** | Porcentaje en número grande en la bandeja, marco amarillo mientras carga. Avisos al iniciar o terminar la carga, al llenarse la batería y al 20% y 10%. El icono muestra `II` mientras el ratón está en reposo y se oculta si el ratón no está conectado. |
| **Todos los ajustes en el menú contextual** | Niveles de DPI (valores, nivel activo, número de niveles), tasa de sondeo, antirrebote, motion sync, corrección de ángulo, control de ondulación, rendimiento máximo, modo, color, brillo y velocidad de la iluminación, apagar luces al mover, retardo de apagado, luz indicadora de DPI, modo de largo alcance. Cada escritura se relee del ratón y se verifica. |
| **Cinco preajustes editables** | Juegos, Escritorio, Precisión, Ahorro de batería, Presentación. Aplicar con un clic, guardar los ajustes actuales del ratón en un preajuste, renombrarlo, restablecerlo. Se guardan en `config.json`. |
| **Ayuda** | El submenú Ayuda lista cada ajuste; al pulsar uno aparece una breve explicación como notificación. "Abrir la guía" muestra todas las explicaciones en una ventana desplazable. |
| **Diez idiomas** | Türkçe, English, Español, Français, Deutsch, Русский, 中文, 日本語, 한국어, العربية. Sigue el idioma del sistema y se cambia desde el menú; la elección se recuerda. |
| **Ligera** | Un icono en la bandeja, sin servicio, sin controlador, no escribe nada fuera de su carpeta salvo `config.json`. Puede iniciarse con Windows. |

> Sin relación con el fabricante. El protocolo se obtuvo por ingeniería inversa observando el software del fabricante y solo se ha probado con el **CrossFire AIR V1** (PixArt PAW3325, firmware v2.0, receptor de 2,4 GHz). Úsalo bajo tu propia responsabilidad.

## Instalación

### Opción A: ejecutable listo (no requiere Python)

1. Descarga `ClawTray_<versión>_win64.zip` desde la página de [Releases](https://github.com/Yerlifan/claw-crossfire-air-tray/releases) y descomprímelo en cualquier carpeta.
2. Ejecuta `ClawTray.exe`. El icono aparece en la bandeja (quizá bajo la flecha `^`).
3. Opcional, accesos directos en el menú Inicio, el escritorio y el inicio de Windows:
   ```powershell
   powershell -ExecutionPolicy Bypass -File kurulum.ps1
   ```

Windows SmartScreen puede avisar la primera vez porque el ejecutable no está firmado; elige *Más información, Ejecutar de todas formas* o usa la opción B.

### Opción B: desde el código fuente

Requisitos: Windows 10/11 (o Linux, ver opción C), Python 3.10 o superior.

```powershell
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
pip install -r requirements.txt
pythonw claw_tray.py
```

Para desinstalar: `kurulum.ps1 -Kaldir` y borra la carpeta. Línea de comandos: `--status` muestra el estado, `--lang es` fuerza el idioma, `--guide` abre la guía.

### Opción C: Linux (beta, aún sin probar en hardware real)

El ratón no necesita controlador en Linux; esta aplicación solo añade la interfaz de batería y ajustes en la bandeja. La adaptación a Linux solo pudo verificarse en una máquina virtual sin el ratón conectado; se agradecen informes desde hardware real.

```bash
./linux/kurulum.sh        # regla udev (sudo), paquetes pip, .desktop + autoinicio
```

Paquetes en Debian/Ubuntu: `sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 python3-tk`; en GNOME activa además la extensión *AppIndicator*. Desinstalar: `./linux/kurulum.sh -u`.

## Conviene saber

- **No funciona junto al software CrossFire.** Si ambos hablan con el ratón a la vez, CrossFire se cierra (el ratón no se ve afectado); por eso la aplicación se pausa mientras CrossFire está abierto (icono `!`). Puedes desinstalar CrossFire; esta aplicación no depende de él.
- No se pueden escribir ajustes mientras el ratón está en reposo (un minuto sin moverse): el icono muestra `II` y se recupera al mover el ratón.
- Si algo sale mal, *Restore* en el software del fabricante devuelve el ratón a los valores de fábrica.
- Las macros y la reasignación de botones quedan fuera del alcance a propósito.

## Detalles del protocolo

El formato de los paquetes, la tabla de comandos y el mapa de la memoria de ajustes están documentados en el [README en inglés](README.md#how-it-works). `claw_proto.py` es toda la capa de protocolo y puede usarse por separado.

## Licencia

MIT, ver [LICENSE](LICENSE).
