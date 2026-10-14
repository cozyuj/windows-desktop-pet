@echo off
chcp 65001 >nul
REM ============================================================
REM  Desktop Pet - Windows 단일 exe 빌드 스크립트
REM  요구사항: Python 3.10+ (python.org 설치판, tkinter 포함)
REM  결과물:   dist\DesktopPet.exe  (파이썬 내장, 콘솔 창 없음)
REM ============================================================
cd /d "%~dp0"

echo [1/4] 가상환경 준비
if not exist .venv (
    python -m venv .venv || goto :fail
)
call .venv\Scripts\activate.bat

echo [2/4] 의존성 설치
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt || goto :fail

echo [3/4] 기본 이미지/아이콘 생성
python make_assets.py || goto :fail

echo [4/4] PyInstaller 빌드
pyinstaller --noconfirm --clean --onefile --windowed ^
    --name DesktopPet ^
    --icon assets\pet.ico ^
    --add-data "assets\pet.png;assets" ^
    desktop_pet.py || goto :fail

copy /Y quotes.txt dist\quotes.txt >nul

set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
    echo [5/5] 설치 프로그램 빌드 ^(Inno Setup^)
    if not exist installer\Korean.isl (
        curl -sL -o installer\Korean.isl https://raw.githubusercontent.com/jrsoftware/issrc/main/Files/Languages/Unofficial/Korean.isl
    )
    %ISCC% /DAppVersion=1.0.0 installer\DesktopPet.iss >nul && echo 설치 프로그램: dist\DesktopPet-Setup.exe
) else (
    echo [5/5] Inno Setup 이 없어 설치 프로그램은 건너뜁니다. ^(https://jrsoftware.org/isdl.php^)
)
echo.
echo 빌드 완료: dist\DesktopPet.exe
echo (dist\quotes.txt 를 exe 옆에 두면 말풍선 문구를 바꿀 수 있습니다)
pause
exit /b 0

:fail
echo.
echo 빌드 실패. 위 오류 메시지를 확인하세요.
pause
exit /b 1
