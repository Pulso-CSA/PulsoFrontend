@echo off
chcp 65001 >nul
title Pulso - Build e publicar release no GitHub

cd /d "%~dp0"

REM Descomente a linha abaixo e coloque seu token (ou deixe GH_TOKEN definido nas variáveis de ambiente do Windows)
REM set GH_TOKEN=seu_token_aqui

if "%GH_TOKEN%"=="" (
    echo [AVISO] GH_TOKEN nao definido. Defina nas variaveis de ambiente do Windows
    echo ou descomente e preencha a linha "set GH_TOKEN=seu_token_aqui" neste arquivo.
    echo.
    set /p CONTINUAR="Publicar mesmo assim? (s/N): "
    if /i not "%CONTINUAR%"=="s" exit /b 1
)

echo.
echo Build do Electron + publicacao no GitHub (Releases)...
echo.

call npm run build:electron:publish

if %ERRORLEVEL% neq 0 (
    echo.
    echo Build/publicacao falhou. Verifique os erros acima.
    pause
    exit /b 1
)

echo.
echo Concluido. A nova versao deve aparecer em: https://github.com/Pulso-CSA/PulsoFrontend/releases
echo.
pause
