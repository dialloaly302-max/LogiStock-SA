@echo off
chcp 65001 >nul
echo Demarrage de LogiStock SA...

if not exist "C:\xampp\htdocs\logistock\index.html" (
  if exist "%~dp0frontend\index.html" (
    if not exist "C:\xampp\htdocs\logistock" mkdir "C:\xampp\htdocs\logistock"
    xcopy /E /I /Y "%~dp0frontend\*" "C:\xampp\htdocs\logistock\" >nul
  )
)

setlocal EnableDelayedExpansion
set "SHADE_JAR=%~dp0backend\target\logistock-simple-1.0.0.jar"
set "SIMPLE_JAR=%~dp0backend\LogiStockServer.jar"

if exist "%SHADE_JAR%" (
  start "LogiStock Backend Java" /min java -jar "%SHADE_JAR%"
) else if exist "%SIMPLE_JAR%" (
  set "CP=%SIMPLE_JAR%"
  for %%j in ("%~dp0backend\lib\*.jar") do set "CP=!CP!;%%j"
  start "LogiStock Backend Java" /min java -cp "!CP!" com.logistock.LogiStockServer
) else (
  where mvn >nul 2>nul
  if not errorlevel 1 (
    pushd "%~dp0backend"
    call mvn clean package
    popd
    if exist "%SHADE_JAR%" (
      start "LogiStock Backend Java" /min java -jar "%SHADE_JAR%"
    )
  ) else (
    if not exist "%~dp0backend\classes" mkdir "%~dp0backend\classes"
    set "CP=%~dp0backend\classes"
    for %%j in ("%~dp0backend\lib\*.jar") do set "CP=!CP!;%%j"
    javac -encoding UTF-8 -cp "!CP!" -d "%~dp0backend\classes" "%~dp0backend\src\main\java\com\logistock\LogiStockServer.java"
    if not errorlevel 1 (
      jar cfe "%SIMPLE_JAR%" com.logistock.LogiStockServer -C "%~dp0backend\classes" .
      start "LogiStock Backend Java" /min java -cp "%CP%;%SIMPLE_JAR%" com.logistock.LogiStockServer
    ) else (
      echo Attention : impossible de compiler automatiquement. Verifiez Maven ou placez mysql-connector-j.jar dans backend\lib.
    )
  )
)

timeout /t 3 >nul
start http://localhost/logistock/
echo.
echo SUR LE TELEPHONE (meme Wi-Fi), ouvrez l'une de ces adresses :
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do echo   http://%%a/logistock/
echo.
pause
