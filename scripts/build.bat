@echo off
REM Build a new Mod Builder - Revived executable for Windows
rmdir /s /q build 2>nul
rmdir /s /q dist\modbuilder 2>nul
pyinstaller modbuilder.spec
