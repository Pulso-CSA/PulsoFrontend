@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0\.."

echo.
echo ============================================================
echo   PulsoFrontend - Release patch ^(um unico passo^)
echo   Bump de versao + push main + tag v* ^(dispara GitHub Actions^)
echo ============================================================
echo.

REM Git/npm costumam nao estar no PATH do cmd.exe; tenta pastas padrao do Windows
call :ENSURE_GIT_IN_PATH
if errorlevel 1 goto :FAIL

call :ENSURE_NPM_IN_PATH
if errorlevel 1 goto :FAIL

for /f %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%i"
if not defined BRANCH (
  echo [X] ERRO: Nao foi possivel identificar a branch atual.
  goto :FAIL
)

if /i not "%BRANCH%"=="main" if /i not "%BRANCH%"=="master" (
  echo [X] ERRO: Execute na branch main ou master ^(atual: %BRANCH%^).
  echo     git checkout main
  echo     git pull origin main
  goto :FAIL
)

echo [OK] Branch permitida: %BRANCH%
echo.

REM Working tree limpa (evita release com alteracoes nao commitadas)
for /f "delims=" %%a in ('git status --porcelain 2^>nul') do (
  echo [X] ERRO: Ha alteracoes nao commitadas. Faca commit ou descarte antes.
  echo     git status
  goto :FAIL
)
echo [OK] Working tree limpa.
echo.

echo ---------- PASSO 1/6: sincronizar com origin ----------
git fetch origin
if errorlevel 1 (
  echo [X] ERRO: git fetch falhou ^(rede ou remote origin^).
  goto :FAIL
)
git pull --ff-only origin %BRANCH%
if errorlevel 1 (
  echo [X] ERRO: git pull --ff-only falhou. Resolva na mao ^(merge/rebase^) e tente de novo.
  goto :FAIL
)
echo [OK] Branch atualizada com origin/%BRANCH%.
echo.

REM Calculo da versao via .ps1 ^(evita CMD corromper -Command com ^-f / caracteres especiais^)
for /f "usebackq delims=" %%i in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bump-patch-version.ps1"`) do set "NEW_VERSION=%%i"
if not defined NEW_VERSION (
  echo [X] ERRO: Nao foi possivel calcular a proxima versao ^(package.json ou bump-patch-version.ps1^).
  goto :FAIL
)
echo !NEW_VERSION!| findstr /r "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul
if errorlevel 1 (
  echo [X] ERRO: Versao calculada invalida: "!NEW_VERSION!"
  goto :FAIL
)
set "NEW_TAG=v!NEW_VERSION!"

set "REMOTE_TAG="
for /f "delims=" %%a in ('git ls-remote origin "refs/tags/!NEW_TAG!" 2^>nul') do set "REMOTE_TAG=%%a"
if defined REMOTE_TAG (
  echo [X] ERRO: A tag !NEW_TAG! JA EXISTE no GitHub.
  echo     Nada foi alterado. Possiveis causas:
  echo     - Voce ja rodou o release antes; veja Actions e Releases no repositorio.
  echo     - Se o workflow falhou, corrija-o e suba outra versao ^(o script fara bump automatico^).
  goto :FAIL
)

echo Proxima versao: !NEW_VERSION!  ^|  Tag: !NEW_TAG!
echo.

echo ---------- PASSO 2/6: npm version ^(package.json + lock^) ----------
call npm version !NEW_VERSION! --no-git-tag-version
if errorlevel 1 (
  echo [X] ERRO: npm version falhou.
  goto :FAIL
)
echo [OK] Versao gravada em package.json / package-lock.json.
echo.

echo ---------- PASSO 3/6: commit ----------
git add package.json package-lock.json 2>nul
git diff --cached --quiet
if not errorlevel 1 (
  echo [X] ERRO: Nada para commitar ^(package.json nao mudou?^).
  goto :FAIL
)
git commit -m "chore(release): !NEW_TAG!"
if errorlevel 1 (
  echo [X] ERRO: git commit falhou.
  goto :FAIL
)
echo [OK] Commit criado: chore^(release^): !NEW_TAG!
echo.

echo ---------- PASSO 4/6: push da branch ----------
git push origin %BRANCH%
if errorlevel 1 (
  echo [X] ERRO: git push origin %BRANCH% falhou ^(permissao, rede ou branch protegida^).
  goto :FAIL
)
echo [OK] Push origin %BRANCH% concluido.
echo.

echo ---------- PASSO 5/6: tag local ----------
git rev-parse "!NEW_TAG!" >nul 2>nul
if not errorlevel 1 (
  echo [!] Tag local !NEW_TAG! ja existia; removendo para recriar no commit atual...
  git tag -d "!NEW_TAG!"
)
git tag "!NEW_TAG!"
if errorlevel 1 (
  echo [X] ERRO: git tag falhou.
  goto :FAIL
)
echo [OK] Tag local !NEW_TAG! aponta para o commit atual.
echo.

echo ---------- PASSO 6/6: push da tag ^(dispara o workflow Release^) ----------
git push origin "!NEW_TAG!"
if errorlevel 1 (
  echo [X] ERRO: git push origin !NEW_TAG! falhou.
  echo     Removendo tag local para nao confundir: git tag -d !NEW_TAG!
  git tag -d "!NEW_TAG!" 2>nul
  goto :FAIL
)
echo [OK] Tag !NEW_TAG! enviada para origin.
echo.

set "ACTIONS_URL="
for /f "usebackq delims=" %%U in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0github-actions-url.ps1"`) do set "ACTIONS_URL=%%U"

echo ============================================================
echo   SUCESSO - Release disparada
echo ============================================================
echo   Versao:  !NEW_VERSION!
echo   Tag:     !NEW_TAG!
echo   Branch:  %BRANCH%
echo.
if defined ACTIONS_URL (
  echo   Acompanhe o build ^(pode levar varios minutos^):
  echo   !ACTIONS_URL!
  echo.
  echo   Se nada aparecer, confira em GitHub:
  echo   - Settings ^> Actions ^> permitido para este repo
  echo   - Aba Actions com filtro workflow "Release"
) else (
  echo   Abra no GitHub: Repositorio ^> Actions ^(workflow "Release" ao receber tag v*^)
)
echo ============================================================
echo.
exit /b 0

:FAIL
echo.
echo ============================================================
echo   FALHA - nenhuma tag nova foi enviada
echo ============================================================
echo.
exit /b 1

:ENSURE_GIT_IN_PATH
where git >nul 2>nul
if not errorlevel 1 exit /b 0
set "GIT_CMD="
if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT_CMD=%ProgramFiles%\Git\cmd"
if not defined GIT_CMD if exist "%ProgramFiles(x86)%\Git\cmd\git.exe" set "GIT_CMD=%ProgramFiles(x86)%\Git\cmd"
if not defined GIT_CMD if exist "%LocalAppData%\Programs\Git\cmd\git.exe" set "GIT_CMD=%LocalAppData%\Programs\Git\cmd"
if not defined GIT_CMD if exist "%UserProfile%\scoop\apps\git\current\cmd\git.exe" set "GIT_CMD=%UserProfile%\scoop\apps\git\current\cmd"
if defined GIT_CMD set "PATH=%GIT_CMD%;%PATH%"
where git >nul 2>nul
if not errorlevel 1 exit /b 0
echo [X] ERRO: Git nao encontrado no PATH.
echo     O Prompt de Comando nao enxerga o Git. Opcoes:
echo     - Use o terminal integrado do Cursor/VS Code ^(geralmente ja inclui Git^); ou
echo     - Instale Git for Windows: https://git-scm.com/download/win ; ou
echo     - Em Variaveis de ambiente, adicione ao PATH: C:\Program Files\Git\cmd
exit /b 1

:ENSURE_NPM_IN_PATH
where npm >nul 2>nul
if not errorlevel 1 exit /b 0
set "NODE_DIR="
if exist "%ProgramFiles%\nodejs\npm.cmd" set "NODE_DIR=%ProgramFiles%\nodejs"
if not defined NODE_DIR if exist "%LocalAppData%\Programs\nodejs\npm.cmd" set "NODE_DIR=%LocalAppData%\Programs\nodejs"
if not defined NODE_DIR if exist "%ProgramFiles%\nodejs\node.exe" set "NODE_DIR=%ProgramFiles%\nodejs"
if defined NODE_DIR set "PATH=%NODE_DIR%;%PATH%"
where npm >nul 2>nul
if not errorlevel 1 exit /b 0
echo [X] ERRO: npm nao encontrado no PATH.
echo     Instale Node.js LTS ^(https://nodejs.org^) ou adicione a pasta do Node ao PATH.
exit /b 1
