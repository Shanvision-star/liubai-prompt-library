param([switch]$ServerOnly)
$ErrorActionPreference = 'Stop'
try {
    $libraryRoot = Split-Path -Parent $PSScriptRoot
    $runtimeDir = Join-Path $PSScriptRoot '.runtime'
    $serverFile = Join-Path $PSScriptRoot 'server.py'
    $appUrl = 'http://127.0.0.1:8767'
    New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
    $health = $null
    try { $health = Invoke-RestMethod -Uri "$appUrl/api/health" -TimeoutSec 2 } catch {}
    if ($health -and ($health.app -ne 'prompt-library-desktop' -or $health.library_root -ne $libraryRoot)) {
        throw 'Port 8767 belongs to another app or library. Please close that app or change the configured port.'
    }
    if (-not $health) {
        $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
        $pythonCandidates = @()
        if ($pythonCommand) { $pythonCandidates += $pythonCommand.Source }
        $pythonCandidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe')
        $pythonCandidates += (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
        $pythonExe = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if (-not $pythonExe) { throw 'Python 3 was not found. Install Python 3, then try again.' }
        $pythonWindowless = Join-Path (Split-Path -Parent $pythonExe) 'pythonw.exe'
        if (Test-Path -LiteralPath $pythonWindowless) { $pythonExe = $pythonWindowless }
        $serverArgument = '"' + $serverFile + '"'
        $rootArgument = '"' + $libraryRoot + '"'
        $arguments = @($serverArgument, '--port', '8767', '--data-root', $rootArgument)
        $serverProcess = Start-Process -FilePath $pythonExe -ArgumentList $arguments -WorkingDirectory $libraryRoot -WindowStyle Hidden -PassThru
        @{ pid = $serverProcess.Id; server = $serverFile; url = $appUrl } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeDir 'server-process.json') -Encoding UTF8
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            Start-Sleep -Milliseconds 200
            try { $health = Invoke-RestMethod -Uri "$appUrl/api/health" -TimeoutSec 1; break } catch {}
            if ($serverProcess.HasExited) { throw "The local server could not start. See $runtimeDir\server.log" }
        }
        if (-not $health -or $health.app -ne 'prompt-library-desktop' -or $health.library_root -ne $libraryRoot) { throw 'The library service did not become ready.' }
    }
    if ($ServerOnly) { Write-Output $appUrl; exit 0 }
    $browserCandidates = @(
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe')
    )
    $browserExe = $browserCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $browserExe) { throw 'Microsoft Edge or Google Chrome is required for the desktop window.' }
    $profileDir = Join-Path $runtimeDir 'browser-profile'
    # 用户明确要求打开可交互的桌面窗口，服务进程仍在后台运行。
    $profileArgument = '--user-data-dir="' + $profileDir + '"'
    Start-Process -FilePath $browserExe -ArgumentList @("--app=$appUrl", $profileArgument, '--no-first-run', '--no-default-browser-check', '--window-size=1440,960')
} catch {
    if ($ServerOnly) { throw }
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Prompt Library') | Out-Null
    exit 1
}
