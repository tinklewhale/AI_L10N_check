@echo off
chcp 65001 >nul
cd /d "%~dp0"
pyinstaller --onefile --windowed --name "AI번역검수도구" gui_app.py
echo.
echo 빌드 완료! dist 폴더에 실행 파일이 생성되었습니다.
pause

