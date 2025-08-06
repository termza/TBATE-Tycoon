@echo off
@echo.
@echo Running the bot...
python main.py
@echo.
@echo -------
@echo.
pause
@echo Bot has stopped running.
@echo Please ensure you have set your DISCORD_TOKEN in the .env file.
@echo.
@echo Press any key to exit...
set /p dummy=Press any key to exit...
pause >nul
exit /b 0