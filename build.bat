@echo off

REM Build the application
pyinstaller --name "valorant-zone-stats" --icon resources/ui/favicon.ico --add-data resources/maps;resources/maps --add-data resources/ui;resources/ui --windowed --noconfirm src/app.py

REM Remove unnecessary dlls
cd "dist\valorant-zone-stats"
del "d3dcompiler_47.dll"
del "opengl32sw.dll"
del "Qt5Pdf.dll"
del "Qt5Quick.dll"
del "libGLESv2.dll"
del "Qt5VirtualKeyboard.dll"
del "Qt5QmlModels.dll"
del "Qt5DBus.dll"
del "Qt5Svg.dll"
del "Qt5WebSockets.dll"

REM pyinstaller --name "valorant-zone-stats" --icon resources/ui/favicon.ico --noconfirm valorant-zone-stats.spec