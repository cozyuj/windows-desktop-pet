# Desktop Pet (윈도우 바탕화면 펫)

바탕화면 위에 떠 있는 작은 감성/유머 펫입니다. 파이썬이 내장된 단일 `DesktopPet.exe` 로
배포되며, 실행하면 콘솔 창 없이 조용히 바탕화면에 나타납니다.

## 기능

| 조작 | 동작 |
|---|---|
| 왼쪽 드래그 | 펫 이동 |
| 왼쪽 클릭 (드래그 없이) | 랜덤 한마디 (펫 위에 텍스트로 표시) |
| Ctrl + 마우스 휠 | 크기 조절 |
| 우클릭 | 메뉴 열기 |
| Esc | 종료 |

우클릭 메뉴
- **이미지 불러오기** : PNG / GIF(애니메이션) / JPG / WEBP / BMP
- **크기** : 50% ~ 300%, 조금 크게/작게
- **위치 조정** : 모서리 4곳, 화면 중앙, 좌표 직접 입력
- **마우스 따라다니기** : 커서를 부드럽게 쫓아오고, 이동 방향으로 얼굴을 돌림
- **좌우 반전 / 둥실둥실 효과 / 항상 위에 표시**
- **클릭하면 한마디** : 클릭할 때 한마디 표시 (기본 켜짐)
- **종료**

마지막에 쓰던 이미지, 위치, 크기, 옵션은 `%APPDATA%\DesktopPet\config.json` 에 저장되어
다음 실행 때 그대로 복원됩니다. exe 옆에 `quotes.txt` 를 두면 말풍선 문구를 바꿀 수 있습니다.

## 그냥 쓰고 싶은 사람 (설치 방법)

https://github.com/cozyuj/windows-desktop-pet/releases/latest 에서 둘 중 하나를 받습니다.

- **DesktopPet-Setup.exe** (권장) : 설치 프로그램. 시작 메뉴 등록, 바탕화면 바로가기,
  윈도우 시작 시 자동 실행 옵션, 제거 프로그램 포함. 관리자 권한 필요 없음.
- **DesktopPet.exe** : 설치 없이 그냥 실행되는 단일 파일.

더블클릭했을 때 "Windows의 PC 보호" 창이 뜨면 **추가 정보 → 실행** 을 누르세요.
바탕화면에 펫이 나타나면 우클릭으로 이미지 변경/설정/종료할 수 있습니다.

## 윈도우에서 exe 만들기 (개발자용)

1. https://www.python.org 에서 Python 3.10 이상 설치 (기본 옵션이면 tkinter 포함)
2. 이 폴더에서 `build.bat` 더블클릭
3. `dist\DesktopPet.exe` 생성

exe 하나만 다른 PC로 복사해도 실행됩니다. 처음 실행은 내장 파이썬을 임시 폴더에 풀기 때문에
2~3초 정도 걸릴 수 있습니다.

### 맥/리눅스에서 윈도우 exe 뽑기

PyInstaller 는 크로스 컴파일을 지원하지 않으므로, GitHub 저장소에 올리면
`.github/workflows/build.yml` 이 윈도우 러너에서 자동 빌드하고 `DesktopPet-windows`
아티팩트로 exe 를 올려줍니다. (Actions 탭 → 워크플로 실행 → Artifacts 다운로드)

## 개발 중 바로 실행해 보기

```bash
python -m venv .venv
.venv\Scripts\activate        # 맥/리눅스: source .venv/bin/activate
pip install pillow
python make_assets.py
python desktop_pet.py
```

## 윈도우 시작 시 자동 실행

설치 프로그램에서 "윈도우 시작할 때 자동으로 실행" 을 체크하면 됩니다.
단일 exe 를 쓰는 경우는 `Win + R` → `shell:startup` → 열리는 폴더에 `DesktopPet.exe` 바로가기를 넣으면 됩니다.

## 참고

- 투명 배경은 윈도우의 키컬러(`#ff00fe`) 방식입니다. 이미지에 정확히 이 색이 있으면 그 부분이 뚫려 보입니다.
- 반투명(그림자 등) 픽셀은 1비트 투명이라 테두리가 살짝 뭉개질 수 있습니다. 가장자리가 또렷한 PNG/GIF 를 권장합니다.
