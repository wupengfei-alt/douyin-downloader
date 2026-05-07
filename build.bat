@echo off
chcp 65001 >nul
echo ==================================================
echo   抖音视频无水印下载器 - PyInstaller 打包脚本
echo ==================================================
echo.

REM 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查 f2 是否安装
python -c "import f2" >nul 2>&1
if errorlevel 1 (
    echo [提示] 未检测到 f2，是否要自动安装？ (Y/N)
    set /p install_f2=
    if /i "!install_f2!"=="Y" (
        echo 正在安装 f2...
        pip install f2
    ) else (
        echo 跳过 f2 安装，程序运行时可能报错。
    )
)

REM 检查 PyInstaller 是否安装
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [提示] 未检测到 PyInstaller，正在安装...
    pip install pyinstaller
)

echo.
echo [步骤 1/2] 打包中...
python -m PyInstaller "抖音下载器.spec"

echo.
if exist "dist\抖音下载器.exe" (
    echo ==================================================
    echo   打包成功！
    echo   输出路径: %cd%\dist\抖音下载器\
    echo ==================================================
) else (
    echo ==================================================
    echo   打包失败，请检查上方错误信息
    echo ==================================================
)

echo.
pause
