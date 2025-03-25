echo off
setlocal enabledelayedexpansion
set "CONFIG_FILE=%CD%\setup.cfg"
for /f "tokens=2 delims==" %%A in ('findstr /i "version" "%CONFIG_FILE%"') do (
    set "VERSION=%%A"
)
set "VERSION=%VERSION: =%"
echo Version: %VERSION%
del /q "%CD%\dist\modbuilder.7z"
"C:\Program Files\7-Zip\7z.exe" a "%CD%\dist\modbuilder_%VERSION%.7z" "%CD%\dist\modbuilder"