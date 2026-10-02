param([string]$Python, [string]$AltiumExe, [switch]$RegisterUserMcp)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskRuntime = Join-Path $taskRoot 'runtime'
$taskPython = Join-Path $taskRoot '.venv/Scripts/python.exe'
$taskLock = Join-Path $taskRoot 'requirements.lock.txt'
New-Item -ItemType Directory -Force -Path $taskRuntime | Out-Null
if (!(Test-Path -LiteralPath $taskPython)) {
    if ($Python) {
        & $Python -m venv (Join-Path $taskRoot '.venv')
    } else {
        & py -3.13 -m venv (Join-Path $taskRoot '.venv')
    }
    if ($LASTEXITCODE -ne 0) { throw 'Install Windows Python 3.13 or pass -Python <python.exe>.' }
}
$taskHash = (Get-FileHash -LiteralPath $taskLock -Algorithm SHA256).Hash
$taskStampFile = Join-Path $taskRuntime 'dependencies.sha256'
$taskInstalledHash = if (Test-Path -LiteralPath $taskStampFile) { (Get-Content -LiteralPath $taskStampFile -Raw).Trim() } else { '' }
if ($taskHash -ne $taskInstalledHash) {
    # Setup output must never contaminate the MCP stdio protocol.
    $ErrorActionPreference = 'Continue'
    & $taskPython -m pip install --disable-pip-version-check -r $taskLock 2>&1 | ForEach-Object { [Console]::Error.WriteLine($_.ToString()) }
    $ErrorActionPreference = 'Stop'
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed; no success stamp was written.' }
    & $taskPython -m pip check | ForEach-Object { [Console]::Error.WriteLine($_.ToString()) }
    if ($LASTEXITCODE -ne 0) { throw 'Dependency validation failed.' }
    [IO.File]::WriteAllText($taskStampFile,$taskHash,[Text.UTF8Encoding]::new($false))
}
$taskConfig = Join-Path $taskRoot 'bridge_config.json'
if ($AltiumExe) {
    if (!(Test-Path -LiteralPath $AltiumExe -PathType Leaf)) { throw 'Altium executable does not exist.' }
    $taskConfigText = @{altium_exe=[IO.Path]::GetFullPath($AltiumExe)} | ConvertTo-Json
    [IO.File]::WriteAllText($taskConfig,$taskConfigText,[Text.UTF8Encoding]::new($false))
} elseif (!(Test-Path -LiteralPath $taskConfig)) {
    Copy-Item -LiteralPath (Join-Path $taskRoot 'bridge_config.example.json') -Destination $taskConfig
}
if ($RegisterUserMcp) {
    & $taskPython (Join-Path $taskRoot 'register_mcp.py') | ForEach-Object { [Console]::Error.WriteLine($_.ToString()) }
    if ($LASTEXITCODE -ne 0) { throw 'MCP registration failed.' }
}
[Console]::Error.WriteLine("Altium tools ready: $taskRoot")
