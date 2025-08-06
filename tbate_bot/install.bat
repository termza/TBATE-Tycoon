@echo off
@echo.
@echo Installing required packages...
pip install discord.py python-dotenv
@echo.
@echo Installation complete.
@echo Please ensure you have set your DISCORD_TOKEN in the .env file.
@echo.
@echo Press any key to continue...
set /p dummy=Press any key to continue...
pause