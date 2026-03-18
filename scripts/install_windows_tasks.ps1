$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\\Scripts\\python.exe"
$publishScript = Join-Path $repo "scripts\\publish_gh_pages.py"
$logs = Join-Path $repo "logs"

New-Item -ItemType Directory -Force -Path $logs | Out-Null

$publishLog = Join-Path $logs "publish.log"

$publishCmd = "cmd.exe /c `"$python`" `"$publishScript`" >> `"$publishLog`" 2>&1"

cmd /c 'schtasks /Delete /TN "KindleFamilyBoardGenerate" /F 2>nul' | Out-Null
cmd /c 'schtasks /Delete /TN "KindleFamilyBoardServer" /F 2>nul' | Out-Null
schtasks /Create /TN "KindleFamilyBoardPublish" /SC DAILY /ST 06:55 /TR $publishCmd /F | Out-Null

Write-Output "Installed scheduled tasks:"
Write-Output "  KindleFamilyBoardPublish at 06:55 daily"
