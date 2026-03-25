# Saida: proxima versao semver (apenas X.Y.Z), uma linha. Usado por release-patch.bat
$ErrorActionPreference = "Stop"
$pkgPath = Join-Path (Split-Path $PSScriptRoot -Parent) "package.json"
if (-not (Test-Path -LiteralPath $pkgPath)) {
  Write-Error "package.json nao encontrado: $pkgPath"
  exit 1
}
$json = Get-Content -Raw -LiteralPath $pkgPath | ConvertFrom-Json
$v = [string]$json.version
if ($v -notmatch '^\d+\.\d+\.\d+$') {
  Write-Error "package.json version invalida (esperado X.Y.Z): $v"
  exit 1
}
$parts = $v.Split(".")
$major = [int]$parts[0]
$minor = [int]$parts[1]
$patch = [int]$parts[2] + 1
Write-Output ("{0}.{1}.{2}" -f $major, $minor, $patch)
exit 0
