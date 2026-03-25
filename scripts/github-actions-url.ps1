# Saida: URL da aba Actions no GitHub, ou linha vazia
$ErrorActionPreference = "Stop"
$u = (git remote get-url origin).Trim()
$m = [regex]::Match($u, "github\.com[:/]([^/]+)/(.+)")
if (-not $m.Success) { exit 0 }
$owner = $m.Groups[1].Value
$repo = ($m.Groups[2].Value -replace "\.git$", "").TrimEnd("/")
Write-Output ("https://github.com/{0}/{1}/actions" -f $owner, $repo)
exit 0
