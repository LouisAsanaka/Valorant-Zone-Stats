@echo off

REM Build the application
pyinstaller --name "valorant-zone-stats" --icon resources/ui/favicon.ico --add-data resources/maps;resources/maps --add-data resources/ui;resources/ui --noconfirm --windowed --onefile src/app.py
