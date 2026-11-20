@echo off
chcp 65001 >nul
echo Compilation du backend LogiStock...

where mvn >nul 2>nul
if not errorlevel 1 (
  cd /d "%~dp0backend"
  call mvn clean package
  if not errorlevel 1 (
    echo Compilation Maven reussie !
    pause
    exit /b 0
  )
)

cd /d "%~dp0backend"
if not exist "classes" mkdir "classes"
setlocal EnableDelayedExpansion
set "CP=classes"
for %%j in (lib\*.jar) do set "CP=!CP!;%%j"
javac -encoding UTF-8 -cp "!CP!" -d classes src\main\java\com\logistock\LogiStockServer.java
if errorlevel 1 (
  echo.
  echo Impossible de compiler : ni Maven ni le pilote MySQL (.jar) dans backend\lib n'a ete trouve.
  echo Installez Maven ou placez mysql-connector-j-x.x.x.jar dans backend\lib.
  pause
  exit /b 1
)
jar cfe LogiStockServer.jar com.logistock.LogiStockServer -C classes .
echo Compilation javac reussie !
pause
