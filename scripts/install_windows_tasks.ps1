$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\\Scripts\\python.exe"
$generateScript = Join-Path $repo "scripts\\generate_board.py"
$serveScript = Join-Path $repo "scripts\\serve_output.py"
$logs = Join-Path $repo "logs"

New-Item -ItemType Directory -Force -Path $logs | Out-Null

$generateLog = Join-Path $logs "generate.log"
$serveLog = Join-Path $logs "serve.log"

$generateCmd = "cmd.exe /c `"$python`" `"$generateScript`" >> `"$generateLog`" 2>&1"
$serveCmd = "cmd.exe /c `"$python`" `"$serveScript`" >> `"$serveLog`" 2>&1"

schtasks /Create /TN "KindleFamilyBoardGenerate" /SC DAILY /ST 06:55 /TR $generateCmd /F | Out-Null
schtasks /Create /TN "KindleFamilyBoardServer" /SC ONLOGON /TR $serveCmd /F | Out-Null

Write-Output "Installed scheduled tasks:"
Write-Output "  KindleFamilyBoardGenerate at 06:55 daily"
Write-Output "  KindleFamilyBoardServer at user logon"
