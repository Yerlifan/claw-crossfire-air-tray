# Claw CrossFire AIR: 시스템 트레이 제어

🇹🇷 [Türkçe](README.tr.md) · 🇬🇧 [English](README.md) · 🇪🇸 [Español](README.es.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇷🇺 [Русский](README.ru.md) · 🇨🇳 [中文](README.zh.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 **한국어** · 🇸🇦 [العربية](README.ar.md)

**Claw CrossFire AIR V1** 무선 마우스를 위한 작은 시스템 트레이 앱입니다. 제조사 소프트웨어도 DLL도 필요 없습니다. USB HID로 마우스와 직접 통신합니다. Windows 지원, Linux 지원은 베타입니다.

![트레이 메뉴](docs/screenshot.png)

## 기능

| | |
|---|---|
| **배터리** | 트레이에 큰 숫자로 잔량 표시, 충전 중에는 노란 테두리. 충전 시작과 종료, 완충, 잔량 20%와 10%에서 알림. 마우스가 절전 중이면 아이콘에 `II`가 표시되고, 마우스가 연결되지 않으면 아이콘이 숨겨집니다. |
| **모든 설정을 오른쪽 클릭 메뉴에서** | DPI 단계(값, 현재 단계, 단계 수), 폴링 레이트, 디바운스, 모션 싱크, 각도 보정, 리플 제어, 최고 성능, 조명 모드, 색상, 밝기, 속도, 움직일 때 조명 끄기, 조명 꺼짐 지연, DPI 표시등, 장거리 모드. 모든 쓰기는 마우스에서 다시 읽어 검증합니다. |
| **편집 가능한 프리셋 5개** | 게임, 데스크톱, 정밀, 배터리 절약, 프레젠테이션. 한 번의 클릭으로 적용, 마우스의 현재 설정을 프리셋에 저장, 이름 바꾸기, 기본값 복원. `config.json`에 저장됩니다. |
| **도움말** | 도움말 하위 메뉴에 모든 설정이 나열되며, 클릭하면 짧은 설명이 알림으로 표시됩니다. "가이드 열기"는 모든 설명을 스크롤 가능한 창에 보여 줍니다. |
| **10개 언어** | Türkçe, English, Español, Français, Deutsch, Русский, 中文, 日本語, 한국어, العربية. 시스템 언어를 따르며 메뉴에서 바꿀 수 있고 선택은 기억됩니다. |
| **가벼움** | 트레이 아이콘 하나뿐. 서비스도 드라이버도 없고, `config.json` 외에는 자기 폴더 밖에 아무것도 쓰지 않습니다. 원하면 Windows와 함께 시작합니다. |

> 제조사와 관련이 없습니다. 프로토콜은 제조사 소프트웨어를 관찰하여 역공학으로 얻었으며 **CrossFire AIR V1**(PixArt PAW3325, 펌웨어 v2.0, 2.4 GHz 수신기)에서만 테스트했습니다. 사용에 따른 책임은 본인에게 있습니다.

## 설치

### 방법 A: 실행 파일(Python 불필요)

1. [Releases](https://github.com/Yerlifan/claw-crossfire-air-tray/releases) 페이지에서 `ClawTray_<버전>_win64.zip`을 내려받아 아무 폴더에나 풉니다.
2. `ClawTray.exe`를 실행합니다. 아이콘이 트레이에 나타납니다(`^` 안에 숨어 있을 수 있음).
3. 선택 사항, 시작 메뉴, 바탕 화면, 시작 프로그램 바로 가기:
   ```powershell
   powershell -ExecutionPolicy Bypass -File kurulum.ps1
   ```

실행 파일이 서명되지 않아 처음 실행 시 Windows SmartScreen이 경고할 수 있습니다. "추가 정보, 실행"을 선택하거나 방법 B를 사용하세요.

### 방법 B: 소스에서 실행

요구 사항: Windows 10/11(또는 Linux, 방법 C 참조), Python 3.10 이상.

```powershell
git clone https://github.com/Yerlifan/claw-crossfire-air-tray.git
cd claw-crossfire-air-tray
pip install -r requirements.txt
pythonw claw_tray.py
```

제거: `kurulum.ps1 -Kaldir` 실행 후 폴더 삭제. 명령줄: `--status`는 현재 상태 표시, `--lang ko`는 언어 지정, `--guide`는 가이드 열기.

### 방법 C: Linux(베타, 실제 하드웨어에서는 아직 미검증)

Linux에서 마우스 자체는 드라이버가 필요 없으며, 이 앱은 트레이의 배터리 및 설정 UI만 추가합니다. Linux 이식은 마우스를 연결하지 않은 가상 머신에서만 검증했습니다. 실제 하드웨어에서의 보고를 환영합니다.

```bash
./linux/kurulum.sh        # udev 규칙(sudo), pip 패키지, .desktop + 자동 시작
```

Debian/Ubuntu 패키지: `sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 python3-tk`; GNOME에서는 *AppIndicator* 확장도 켜야 합니다. 제거: `./linux/kurulum.sh -u`.

## 알아 둘 점

- **CrossFire 소프트웨어와 동시에 실행되지 않습니다.** 둘이 동시에 마우스와 통신하면 CrossFire가 종료됩니다(마우스는 영향 없음). 그래서 CrossFire가 실행 중이면 이 앱은 스스로 일시 정지합니다(아이콘 `!`). CrossFire를 제거해도 됩니다. 이 앱은 그것에 의존하지 않습니다.
- 마우스가 절전 중(약 1분간 움직임 없음)이면 설정을 쓸 수 없습니다. 아이콘에 `II`가 표시되고 마우스를 움직이면 바로 회복됩니다.
- 문제가 생기면 제조사 소프트웨어의 *Restore*로 마우스를 공장 초기화할 수 있습니다.
- 매크로와 버튼 재할당은 의도적으로 범위 밖입니다.

## 프로토콜 세부 사항

패킷 형식, 명령 표, 설정 메모리 맵은 [영어 README](README.md#how-it-works)에 문서화되어 있습니다. `claw_proto.py`가 프로토콜 계층 전체이며 단독으로도 쓸 수 있습니다.

## 라이선스

MIT, [LICENSE](LICENSE) 참조.
