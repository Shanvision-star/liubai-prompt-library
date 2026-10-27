param(
    [string]$DataRoot = (Split-Path -Parent $PSScriptRoot),
    [ValidateRange(1, 65535)][int]$Port = 8767
)
$ErrorActionPreference = 'Stop'
$libraryRoot = [System.IO.Path]::GetFullPath($DataRoot)
if (-not (Test-Path -LiteralPath $libraryRoot)) { Write-Output 'No recorded server process.'; exit 0 }
$libraryRoot = (Get-Item -LiteralPath $libraryRoot).FullName
$runtimeDir = Join-Path $libraryRoot 'desktop/.runtime'
$processFile = Join-Path $runtimeDir "server-process-$Port.json"
$legacy = $false
if (-not (Test-Path -LiteralPath $processFile) -and $Port -eq 8767) {
    $processFile = Join-Path $runtimeDir 'server-process.json'
    $legacy = $true
}
if (-not (Test-Path -LiteralPath $processFile)) { Write-Output 'No recorded server process. Stop a terminal-launched server with Ctrl+C.'; exit 0 }
$record = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
$serverProcessId = [int]$record.pid
$process = Get-CimInstance Win32_Process -Filter "ProcessId = $serverProcessId"
if (-not $process) { Write-Output 'The server is already stopped.'; exit 0 }
$expectedServer = Join-Path $PSScriptRoot 'server.py'
$portPattern = '(?:^|\s)--port\s+"?' + $Port + '"?(?:\s|$)'
$identityMatches = $process.Name -match '^pythonw?\.exe$' -and $record.server -eq $expectedServer -and $process.CommandLine.Contains($expectedServer) -and $process.CommandLine -match $portPattern
if (-not $legacy) {
    # PID 可被复用，必须同时核对创建时间、解释器、目录和端口。
    $started = [DateTime]::Parse($record.started_utc).ToUniversalTime()
    $created = $process.CreationDate.ToUniversalTime()
    $identityMatches = $identityMatches -and $record.port -eq $Port -and $record.library_root -eq $libraryRoot -and $process.ExecutablePath -eq $record.python -and [Math]::Abs(($started - $created).TotalSeconds) -lt 1 -and $process.CommandLine.Contains($libraryRoot)
}
if (-not $identityMatches) { throw 'The recorded PID does not match this library server; nothing was stopped.' }
Stop-Process -Id $serverProcessId
Write-Output "Liubai server on port $Port stopped. Desktop windows can be closed normally."
