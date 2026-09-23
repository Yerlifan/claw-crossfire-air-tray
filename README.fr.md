# Claw CrossFire AIR : contrôle depuis la zone de notification

🇹🇷 [Türkçe](README.tr.md) · 🇬🇧 [English](README.md) · 🇪🇸 [Español](README.es.md) · 🇫🇷 **Français** · 🇩🇪 [Deutsch](README.de.md) · 🇷🇺 [Русский](README.ru.md) · 🇨🇳 [中文](README.zh.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇸🇦 [العربية](README.ar.md)

Une petite application de zone de notification pour la souris sans fil **Claw CrossFire AIR V1**. Elle n'a besoin ni du logiciel du fabricant ni de sa DLL : elle parle directement à la souris en USB HID. Windows, avec une prise en charge de Linux en bêta.

![Menu de la zone de notification](docs/screenshot.png)

## Fonctions

| | |
|---|---|
| **Batterie** | Pourcentage en grand dans la zone de notification, cadre jaune pendant la charge. Notifications au début et à la fin de la charge, quand la batterie est pleine, puis à 20% et 10%. L'icône affiche `II` quand la souris est en veille et disparaît quand la souris n'est pas connectée. |
| **Tous les réglages dans le menu contextuel** | Niveaux de DPI (valeurs, niveau actif, nombre de niveaux), taux de rapport, anti rebond, motion sync, correction d'angle, contrôle d'ondulation, performance maximale, mode, couleur, luminosité et vitesse de l'éclairage, extinction en mouvement, délai d'extinction, voyant DPI, mode longue portée. Chaque écriture est relue depuis la souris et vérifiée. |
| **Cinq préréglages modifiables** | Jeu, Bureau, Précision, Économie de batterie, Présentation. Appliquer en un clic, enregistrer les réglages actuels de la souris dans un préréglage, le renommer, le rétablir. Stockés dans `config.json`. |
| **Aide** | Le sous menu Aide liste chaque réglage ; un clic affiche une courte explication en notification. « Ouvrir le guide » affiche toutes les explications dans une fenêtre défilante. |
| **Dix langues** | Türkçe, English, Español, Français, Deutsch, Русский, 中文, 日本語, 한국어, العربية. Suit la langue du système et se change depuis le menu ; le choix est mémorisé. |
| **Légère** | Une icône, pas de service, pas de pilote, rien d'écrit hors de son dossier à part `config.json`. Peut démarrer avec Windows. |

> Sans lien avec le fabricant. Le protocole a été obtenu par rétro ingénierie en observant le logiciel du fabricant et n'a été testé qu'avec la **CrossFire AIR V1** (PixArt PAW3325, firmware v2.0, récepteur 2,4 GHz). À utiliser à vos risques.

## Installation

### Option A : exécutable prêt à l'emploi (Python inutile)

1. Téléchargez `ClawTray_<version>_win64.zip` depuis la page [Releases](https://github.com/Yerlifan/claw-crossfire-air-tray/releases) et décompressez le dans un dossier quelconque.
2. Lancez `ClawTray.exe`. L'icône apparaît dans la zone de notification (parfois sous la flèche `^`).
3. Facultatif, raccourcis dans le menu Démarrer, sur le bureau et au démarrage de Windows :
   ```powershell
   powershell -ExecutionPolicy Bypass -File kurulum.ps1
   ```

Windows SmartScreen peut avertir la première fois car l'exécutable n'est pas signé ; choisissez *Informations complémentaires, Exécuter quand même* ou utilisez l'option B.

### Option B : depuis les sources

Prérequis : Windows 10/11 (ou Linux, voir option C), Python 3.10 ou plus récent.

```powershell
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
pip install -r requirements.txt
pythonw claw_tray.py
```

Désinstallation : `kurulum.ps1 -Kaldir` puis supprimez le dossier. Ligne de commande : `--status` affiche l'état, `--lang fr` force la langue, `--guide` ouvre le guide.

### Option C : Linux (bêta, pas encore testé sur du vrai matériel)

La souris n'a besoin d'aucun pilote sous Linux ; cette application ajoute seulement l'interface batterie et réglages. Le portage Linux n'a pu être vérifié que dans une machine virtuelle sans la souris ; les retours sur du vrai matériel sont bienvenus.

```bash
./linux/kurulum.sh        # règle udev (sudo), paquets pip, .desktop + démarrage automatique
```

Paquets Debian/Ubuntu : `sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 python3-tk` ; sous GNOME activez aussi l'extension *AppIndicator*. Désinstallation : `./linux/kurulum.sh -u`.

## Bon à savoir

- **Ne fonctionne pas en même temps que le logiciel CrossFire.** Si les deux parlent à la souris en même temps, CrossFire plante (la souris n'est pas affectée) ; l'application se met donc en pause tant que CrossFire tourne (icône `!`). Vous pouvez désinstaller CrossFire ; l'application n'en dépend pas.
- Aucun réglage ne peut être écrit pendant la veille de la souris (environ une minute sans mouvement) : l'icône affiche `II` et revient dès que vous bougez la souris.
- En cas de problème, *Restore* dans le logiciel du fabricant remet la souris aux réglages d'usine.
- Les macros et la réaffectation des boutons sont volontairement hors périmètre.

## Détails du protocole

Le format des paquets, la table des commandes et la carte de la mémoire de réglages sont documentés dans le [README en anglais](README.md#how-it-works). `claw_proto.py` constitue toute la couche protocole et peut être utilisé seul.

## Licence

MIT, voir [LICENSE](LICENSE).
