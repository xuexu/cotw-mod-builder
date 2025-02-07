echo off
rmdir /s /q "%CD%\dist\modbuilder"
pyinstaller --noconsole --add-data "%CD%\modbuilder\org;org" --add-data "%CD%\modbuilder\plugins\*.py;plugins" --add-data "%CD%\modbuilder\saves;saves" --add-data "%CD%\deca\*.py;deca" --add-data "%CD%\modbuilder\name_map.yaml;." "%CD%\modbuilder.py"