@echo off
chcp 65001 >nul
echo AI 번역 검수 도구 실행 파일 빌드
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM PyInstaller 설치 확인
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller가 설치되어 있지 않습니다.
    echo 설치 중...
    pip install pyinstaller
)

echo.
echo 실행 파일 빌드 중...
echo.

REM 기존 빌드 파일 정리
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist "AI번역검수도구.spec" del /q "AI번역검수도구.spec"

REM 실행 파일 빌드
pyinstaller --onefile --windowed --name "AI번역검수도구" --icon=NONE --add-data "translation_engine.py;." gui_app.py

if errorlevel 1 (
    echo.
    echo 빌드 실패!
    pause
    exit /b 1
)

echo.
echo 빌드 완료!
echo 실행 파일 위치: dist\AI번역검수도구.exe
echo.
echo 실행 파일을 더블클릭하여 프로그램을 실행할 수 있습니다.
echo.
pause

