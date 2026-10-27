param(
    [switch]$ServerOnly,
    [string]$DataRoot = (Split-Path -Parent $PSScriptRoot),
    [ValidateRange(1, 65535)][int]$Port = 8767
)
$ErrorActionPreference = 'Stop'

function Resolve-LiubaiPython {
    foreach ($name in @('python.exe', 'python3.exe', 'py.exe')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $command) { continue }
        $prefix = @()
        if ($name -eq 'py.exe') { $prefix = @('-3') }
        try {
            # 标准库服务直接使用真实解释器，避免 venv 的 Windows 转发进程留下子进程。
            $probe = & $command.Source @prefix -I -X utf8 -c 'import json,sys; print(json.dumps(dict(executable=getattr(sys, ''_base_executable'', sys.executable),version=list(sys.version_info[:2]))))' 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
            $details = $probe | Select-Object -Last 1 | ConvertFrom-Json
            if (($details.version[0] -gt 3 -or ($details.version[0] -eq 3 -and $details.version[1] -ge 11)) -and (Test-Path -LiteralPath $details.executable)) {
                return $details.executable
            }
        } catch { continue }
    }
    throw 'Python 3.11 or newer was not found. Install it from python.org (include Python or the py launcher in PATH), then try again.'
}

function Quote-LiubaiArgument([string]$Value) {
    # Windows 命令行末尾的反斜线需要加倍，根目录等路径才能正确传入 Python。
    return '"' + ($Value -replace '(\\+)$', '$1$1') + '"'
}

try {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $libraryRoot = [System.IO.Path]::GetFullPath($DataRoot)
    New-Item -ItemType Directory -Force -Path $libraryRoot | Out-Null
    $libraryRoot = (Get-Item -LiteralPath $libraryRoot).FullName
    $runtimeDir = Join-Path $libraryRoot 'desktop/.runtime'
    $serverFile = Join-Path $PSScriptRoot 'server.py'
    $versionSource = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'library_export.py') -Raw
    $expectedVersion = [regex]::Match($versionSource, '(?m)^APP_VERSION\s*=\s*"([^"]+)"').Groups[1].Value
    if (-not $expectedVersion) { throw 'Cannot read the application version. Download a complete release and try again.' }
    $appUrl = "http://127.0.0.1:$Port"
    New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
    $health = $null
    try { $health = Invoke-RestMethod -Uri "$appUrl/api/health" -TimeoutSec 2 } catch {}
    if ($health -and ($health.app -ne 'prompt-library-desktop' -or $health.library_root -ne $libraryRoot)) {
        throw "Port $Port belongs to another app or library. Use the same -DataRoot, or select another -Port."
    }
    if ($health -and $health.version -ne $expectedVersion) {
        throw 'An older server is still running. Stop it with Ctrl+C or its original Stop-Desktop.ps1, then open the updated application.'
    }
    if (-not $health) {
        $probeConnection = New-Object System.Net.Sockets.TcpClient
        try {
            $connection = $probeConnection.ConnectAsync('127.0.0.1', $Port)
            try { $null = $connection.Wait(500) } catch {}
            if ($probeConnection.Connected) { throw "Port $Port is occupied by another service. Select another -Port." }
        } finally { $probeConnection.Dispose() }
        $pythonExe = Resolve-LiubaiPython
        $pythonWindowless = Join-Path (Split-Path -Parent $pythonExe) 'pythonw.exe'
        if (Test-Path -LiteralPath $pythonWindowless) { $pythonExe = $pythonWindowless }
        $arguments = @('-X', 'utf8', (Quote-LiubaiArgument $serverFile), '--port', $Port.ToString(), '--data-root', (Quote-LiubaiArgument $libraryRoot))
        $serverProcess = Start-Process -FilePath $pythonExe -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir "startup-$Port.stdout.log") -RedirectStandardError (Join-Path $runtimeDir "startup-$Port.log")
        $record = @{ pid = $serverProcess.Id; server = $serverFile; url = $appUrl; port = $Port; library_root = $libraryRoot; python = $pythonExe; started_utc = $serverProcess.StartTime.ToUniversalTime().ToString('o') }
        $record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeDir "server-process-$Port.json") -Encoding UTF8
        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            Start-Sleep -Milliseconds 200
            if ($serverProcess.HasExited) { throw "The local server could not start. See $runtimeDir\startup-$Port.log" }
            try { $health = Invoke-RestMethod -Uri "$appUrl/api/health" -TimeoutSec 1; break } catch {}
        }
        if (-not $health -or $health.app -ne 'prompt-library-desktop' -or $health.library_root -ne $libraryRoot -or $health.version -ne $expectedVersion) {
            if (-not $serverProcess.HasExited) { $serverProcess.Kill() }
            throw "The library service did not become ready. See $runtimeDir\startup-$Port.log"
        }
    }
    if ($ServerOnly) { Write-Output $appUrl; exit 0 }
    $browserCandidates = @()
    foreach ($folder in @(${env:ProgramFiles(x86)}, $env:ProgramFiles, $env:LOCALAPPDATA)) {
        if ($folder) {
            $browserCandidates += (Join-Path $folder 'Microsoft/Edge/Application/msedge.exe')
            $browserCandidates += (Join-Path $folder 'Google/Chrome/Application/chrome.exe')
        }
    }
    $browserExe = $browserCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($browserExe) {
        $profileDir = Join-Path $runtimeDir 'browser-profile'
        # 用户启动的是交互窗口；服务进程仍在后台隐藏运行。
        $profileArgument = '--user-data-dir=' + (Quote-LiubaiArgument $profileDir)
        Start-Process -FilePath $browserExe -ArgumentList @("--app=$appUrl", $profileArgument, '--no-first-run', '--no-default-browser-check', '--window-size=1440,960')
    } else {
        Start-Process -FilePath $appUrl
    }
} catch {
    if ($ServerOnly) { throw }
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Liubai') | Out-Null
    exit 1
}
