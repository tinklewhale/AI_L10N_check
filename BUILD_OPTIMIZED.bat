@echo off
chcp 65001 >nul
echo ========================================
echo AI 번역 검수 도구 - 최적화 빌드
echo ========================================
echo.
echo 이 스크립트는 최적화된 실행 파일을 생성합니다.
echo 불필요한 패키지를 제외하여 파일 크기를 줄입니다.
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
echo 기존 빌드 파일 정리 중...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist "AI번역검수도구.spec" del /q "AI번역검수도구.spec"

echo.
echo 최적화된 실행 파일 빌드 중...
echo (이 작업은 몇 분 정도 걸릴 수 있습니다...)
echo.

REM 최적화된 빌드 명령
pyinstaller --onefile ^
    --windowed ^
    --name "AI번역검수도구" ^
    --icon=NONE ^
    --add-data "translation_engine.py;." ^
    --exclude-module matplotlib ^
    --exclude-module scipy ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    --exclude-module notebook ^
    --exclude-module pytest ^
    --exclude-module pylint ^
    --exclude-module black ^
    --exclude-module mypy ^
    --exclude-module sphinx ^
    --exclude-module PyQt5 ^
    --exclude-module PyQt6 ^
    --exclude-module PySide2 ^
    --exclude-module PySide6 ^
    --exclude-module bokeh ^
    --exclude-module plotly ^
    --exclude-module altair ^
    --exclude-module seaborn ^
    --exclude-module sklearn ^
    --exclude-module tensorflow ^
    --exclude-module torch ^
    --exclude-module keras ^
    --exclude-module dask ^
    --exclude-module distributed ^
    --exclude-module panel ^
    --exclude-module holoviews ^
    --exclude-module xarray ^
    --exclude-module intake ^
    --exclude-module statsmodels ^
    --exclude-module patsy ^
    --exclude-module botocore ^
    --exclude-module tables ^
    --exclude-module sqlalchemy ^
    --exclude-module h5py ^
    --exclude-module lz4 ^
    --exclude-module zmq ^
    --exclude-module pyarrow ^
    --exclude-module fsspec ^
    --exclude-module numba ^
    --exclude-module llvmlite ^
    --exclude-module cloudpickle ^
    --exclude-module nbformat ^
    --exclude-module jsonschema ^
    --exclude-module nbconvert ^
    --exclude-module mistune ^
    --exclude-module tinycss2 ^
    --exclude-module yapf_third_party ^
    --exclude-module blib2to3 ^
    --exclude-module bcrypt ^
    --exclude-module argon2 ^
    --exclude-module jupyterlab ^
    --exclude-module ruamel.yaml ^
    --exclude-module anyio ^
    --exclude-module skimage ^
    --exclude-module narwhals ^
    --exclude-module cryptography ^
    --strip ^
    --noupx ^
    gui_app.py

if errorlevel 1 (
    echo.
    echo 빌드 실패!
    pause
    exit /b 1
)

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
echo.
echo 실행 파일 위치: dist\AI번역검수도구.exe

REM 파일 크기 확인
for %%F in ("dist\AI번역검수도구.exe") do (
    set size=%%~zF
    set /a sizeMB=%%~zF/1024/1024
    echo 파일 크기: !sizeMB! MB (%%~zF bytes)
)

echo.
echo 실행 파일을 더블클릭하여 프로그램을 실행할 수 있습니다.
echo.
echo GitHub에 업로드하려면:
echo   git add dist\AI번역검수도구.exe
echo   git commit -m "Update optimized executable"
echo   git push
echo.
pause

