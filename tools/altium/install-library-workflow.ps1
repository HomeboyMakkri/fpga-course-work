# Compatibility entrypoint; source and canonical skill remain in the repository.
param([string]$Python, [string]$AltiumExe, [switch]$SkipMemory)
& (Join-Path $PSScriptRoot 'setup.ps1') -Python $Python -AltiumExe $AltiumExe -RegisterUserMcp
