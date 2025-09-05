@echo off
rem Package Mod Builder - Revived into a versioned 7z archive
setlocal
set "VERSION="
for /f "usebackq tokens=2 delims==" %%A in (`findstr /r /c:"^[ ]*version[ ]*=" pyproject.toml`) do (
  for /f "tokens=* delims= " %%B in ("%%~A") do set "VERSION=%%B"
)
set "VERSION=%VERSION:"=%"

if not defined VERSION (
  echo ERROR: could not parse version from pyproject.toml
  exit /b 1
)

del /q "%CD%\dist\modbuilder.7z" 2>nul
del /q "%CD%\dist\modbuilder_%VERSION%.7z" 2>nul
"C:\Program Files\7-Zip\7z.exe" a "%CD%\dist\modbuilder_%VERSION%.7z" "%CD%\dist\modbuilder"
