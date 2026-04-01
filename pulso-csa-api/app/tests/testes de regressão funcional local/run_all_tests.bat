@echo off
setlocal enabledelayedexpansion

:: ==========================================================
::  🚀 TESTE AUTOMÁTICO – WORKFLOW COMPLETO (Camada 1 + 2)
:: ==========================================================
set LOG_DIR=logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set LOG_FILE=%LOG_DIR%\workflow_full.log
echo ========================================================== > "%LOG_FILE%"
echo 📅 TESTE INICIADO EM: %date% %time% >> "%LOG_FILE%"
echo ========================================================== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo ==========================================================
echo 🧠  INICIANDO WORKFLOW COMPLETO (Camada 1 + 2)
echo ==========================================================
echo. >> "%LOG_FILE%"
echo [INÍCIO] Executando pipeline completo (Camada 1 + 2)... >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

:: ==========================================================
:: 🔹 Teste – Pipeline Completo com único prompt
:: ==========================================================
set PROMPT=criar uma API simples modularizada em Python utilizando Flask, com autenticação JWT
set USER=marcelo.go

echo Executando workflow com prompt:
echo "%PROMPT%"
echo. >> "%LOG_FILE%"
echo === Enviando prompt inicial === >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

curl -s -X POST "http://127.0.0.1:8000/governance/run" ^
-H "Content-Type: application/json" ^
-d "{\"prompt\":\"%PROMPT%\",\"usuario\":\"%USER%\"}" ^
>> "%LOG_FILE%"

echo. >> "%LOG_FILE%"
echo ---------------------------------------------------------- >> "%LOG_FILE%"
echo [✔] Workflow completo executado. >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

:: ==========================================================
:: ✅ Finalização
:: ==========================================================
echo ========================================================== >> "%LOG_FILE%"
echo ✅ TESTE FINALIZADO EM: %date% %time% >> "%LOG_FILE%"
echo ========================================================== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo ==========================================================
echo ✅ Workflow completo executado com sucesso.
echo 📄 Logs salvos em: %LOG_FILE%
echo ==========================================================
pause
endlocal
