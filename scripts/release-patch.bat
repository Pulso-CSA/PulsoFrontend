@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Vai para a raiz do repositório (este arquivo fica em scripts\)
cd /d "%~dp0\.."

echo ==============================================
echo   PulsoFrontend - Release Patch
echo ==============================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Git nao encontrado no PATH.
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERRO] NPM nao encontrado no PATH.
  exit /b 1
)

for /f %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%i"
if not defined BRANCH (
  echo [ERRO] Nao foi possivel identificar a branch atual.
  exit /b 1
)

set "ON_MAIN=0"
if /i "%BRANCH%"=="main" set "ON_MAIN=1"
if /i "%BRANCH%"=="master" set "ON_MAIN=1"

echo Branch atual: %BRANCH%
if "%ON_MAIN%"=="1" (
  echo Modo: main/master — apos o bump sera criada e enviada a tag ^(dispara o GitHub Release^).
) else (
  echo Modo: branch de trabalho — sobe apenas o commit; a tag fica para depois do merge na main.
)
echo.

REM Calcula a proxima versao (patch) com base no package.json atual
for /f %%i in ('powershell -NoProfile -Command "$v=(Get-Content package.json -Raw | ConvertFrom-Json).version; if($v -notmatch ''^\d+\.\d+\.\d+$''){ throw ''Versao invalida em package.json''}; $p=$v.Split(''.''); ''{0}.{1}.{2}'' -f $p[0],$p[1],([int]$p[2]+1)"') do set "NEW_VERSION=%%i"
if not defined NEW_VERSION (
  echo [ERRO] Nao foi possivel calcular a nova versao.
  exit /b 1
)

set "NEW_TAG=v%NEW_VERSION%"
echo Nova versao: %NEW_VERSION%
echo Nova tag: %NEW_TAG% ^(criada apenas na main/master ou via release-push-tag.bat^)
echo.

call npm version %NEW_VERSION% --no-git-tag-version
if errorlevel 1 (
  echo [ERRO] Falha ao atualizar versao via npm.
  exit /b 1
)

git add package.json package-lock.json 2>nul

git diff --cached --quiet
if not errorlevel 1 (
  echo [ERRO] Nenhuma alteracao staged para commit.
  exit /b 1
)

git commit -m "chore(release): %NEW_TAG%"
if errorlevel 1 (
  echo [ERRO] Falha ao criar commit.
  exit /b 1
)

echo.
echo Enviando branch %BRANCH% para origin...
git push origin %BRANCH%
if errorlevel 1 (
  echo [ERRO] Falha no push da branch %BRANCH%.
  exit /b 1
)

if "%ON_MAIN%"=="1" goto TAG_AND_PUSH

echo.
echo [OK] Bump %NEW_TAG% enviado na branch %BRANCH%.
echo.
echo Proximos passos ^(tag so apos codigo na main^):
echo   1. Abra o PR desta branch para main e faca o merge.
echo   2. git checkout main
echo   3. git pull origin main
echo   4. scripts\release-push-tag.bat
echo.
echo Isso cria e envia a tag %NEW_TAG% e dispara o workflow de release.
exit /b 0

:TAG_AND_PUSH
git tag %NEW_TAG%
if errorlevel 1 (
  echo [ERRO] Falha ao criar tag. Ela pode ja existir localmente.
  exit /b 1
)

echo Enviando tag %NEW_TAG%...
git push origin %NEW_TAG%
if errorlevel 1 (
  echo [ERRO] Falha no push da tag %NEW_TAG%.
  exit /b 1
)

echo.
echo [OK] Release publicada a partir da main/master.
echo     Branch: %BRANCH%
echo     Tag:    %NEW_TAG%
exit /b 0
