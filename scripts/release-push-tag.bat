@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Cria e envia a tag v* com base no package.json da branch atual.
REM Use na main (ou master) apos merge do PR do bump de versao.
cd /d "%~dp0\.."

echo ==============================================
echo   PulsoFrontend - Enviar tag de release
echo ==============================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Git nao encontrado no PATH.
  exit /b 1
)

for /f %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%i"
if not defined BRANCH (
  echo [ERRO] Nao foi possivel identificar a branch atual.
  exit /b 1
)

if /i not "%BRANCH%"=="main" if /i not "%BRANCH%"=="master" (
  echo [ERRO] Este script deve ser executado em main ou master.
  echo         Branch atual: %BRANCH%
  echo         Faca: git checkout main ^&^& git pull origin main
  exit /b 1
)

echo Branch: %BRANCH%
echo Atualizando referencias ^(git pull^)...
git pull origin %BRANCH%
if errorlevel 1 (
  echo [ERRO] git pull falhou. Resolva conflitos ou rede e tente de novo.
  exit /b 1
)

for /f %%i in ('powershell -NoProfile -Command "$v=(Get-Content package.json -Raw | ConvertFrom-Json).version; if($v -notmatch ''^\d+\.\d+\.\d+$''){ throw ''Versao invalida'' }; $v"') do set "VER=%%i"
if not defined VER (
  echo [ERRO] Nao foi possivel ler version de package.json.
  exit /b 1
)

set "TAG=v%VER%"
echo Versao em package.json: %VER%
echo Tag a enviar: %TAG%
echo.

git rev-parse "%TAG%" >nul 2>nul
if not errorlevel 1 (
  echo [ERRO] A tag %TAG% ja existe neste repositorio local.
  echo         Apague com: git tag -d %TAG%  ^(se ainda nao foi enviada^)
  exit /b 1
)

set "REMOTE_TAG="
for /f "delims=" %%a in ('git ls-remote origin "refs/tags/%TAG%" 2^>nul') do set "REMOTE_TAG=%%a"
if defined REMOTE_TAG (
  echo [ERRO] A tag %TAG% ja existe no origin. Nada a fazer.
  exit /b 1
)

git tag %TAG%
if errorlevel 1 (
  echo [ERRO] Falha ao criar tag %TAG%.
  exit /b 1
)

git push origin %TAG%
if errorlevel 1 (
  echo [ERRO] Falha no push da tag %TAG%.
  echo         Para remover a tag local: git tag -d %TAG%
  exit /b 1
)

echo.
echo [OK] Tag %TAG% enviada. O workflow Release ^(push tags v*^) deve gerar o instalador.
exit /b 0
