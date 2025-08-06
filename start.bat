@echo off
title TBATE Bot Launcher
chcp 65001 > nul

:menu
cls
color 0D
echo.
echo  ████████╗██████╗  █████╗ ████████╗███████╗
echo  ╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
echo     ██║   ██████╔╝███████║   ██║   █████╗  
echo     ██║   ██╔══██╗██╔══██║   ██║   ██╔══╝  
echo     ██║   ██║  ██║██║  ██║   ██║   ███████╗
echo     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
echo.                                           
echo       ██████╗  ██████╗ ████████╗
echo      ██╔═══██╗██╔═══██╗╚══██╔══╝
echo      ██║   ██║██║   ██║   ██║   
echo      ██║   ██║██║   ██║   ██║   
echo      ╚██████╔╝╚██████╔╝   ██║   
echo       ╚═════╝  ╚═════╝    ╚═╝   
echo.
echo =================================================
echo.
echo            [1] Start Bot
echo            [2] Install/Update Dependencies
echo            [3] Exit
echo.
echo =================================================
echo.
set /p choice="Enter your choice: "

if "%choice%"=="1" goto start_bot
if "%choice%"=="2" goto install_deps
if "%choice%"=="3" exit

goto menu

:start_bot
cls
if not exist .env (
    echo .env file not found. Let's set it up.
    echo.
    set /p token="Please paste your Discord Bot Token and press Enter: "
    echo DISCORD_TOKEN=%token% > .env
    echo.
    echo .env file created successfully!
)
python main.py
pause
goto menu

:install_deps
cls
echo Installing required Python libraries from requirements.txt...
echo.
pip install -r requirements.txt
echo.
echo Dependencies installed successfully.
pause
goto menu