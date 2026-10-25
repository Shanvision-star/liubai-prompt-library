$ErrorActionPreference = 'Stop'
$processFile = Join-Path $PSScriptRoot '.runtime\server-process.json'
if (-not (Test-Path -LiteralPath $processFile)) { Write-Output 'No recorded server process.'; exit 0 }
$record = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
$serverProcessId = [int]$record.pid
$process = Get-CimInstance Win32_Process -Filter "ProcessId = $serverProcessId"
if (-not $process) { Write-Output 'The server is already stopped.'; exit 0 }
$expectedServer = Join-Path $PSScriptRoot 'server.py'
if ($process.Name -notmatch '^pythonw?\.exe$' -or -not $process.CommandLine.Contains($expectedServer) -or -not $process.CommandLine.Contains('--port 8767')) {
    throw 'The recorded PID does not match this library server; nothing was stopped.'
}
Stop-Process -Id $serverProcessId
Write-Output 'Prompt Library server stopped. Desktop windows can be closed normally.'
