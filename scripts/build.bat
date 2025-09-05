@echo off
REM Build a new Mod Builder - Revived executable for Windows
rmdir /s /q "%CD%\build" 2>nul
rmdir /s /q "%CD%\dist\modbuilder" 2>nul
pyinstaller modbuilder.spec
