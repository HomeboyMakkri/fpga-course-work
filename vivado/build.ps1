param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [switch]$Project,
    [string]$Vivado = 'C:\Xilinx\Vivado\2019.1\bin\vivado.bat'
)
$ErrorActionPreference = 'Stop'
# Conservative guard: do not share an .xpr or its sources with an active editor.
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) {
    throw 'Vivado is already running. Save user edits and close Vivado before this build.'
}
$repoRoot = Split-Path $PSScriptRoot -Parent
$outPath = [System.IO.Path]::GetFullPath($OutputDirectory)
if ((Test-Path -LiteralPath $outPath) -and (Get-ChildItem -LiteralPath $outPath -Force)) {
    throw "Output directory must be empty: $outPath"
}
$scriptPath = Join-Path $PSScriptRoot $(if ($Project) {'project_build.tcl'} else {'build.tcl'})
Push-Location $repoRoot
try {
    & $Vivado -mode batch -nojournal -log "$outPath.vivado.log" -source $scriptPath -tclargs $outPath
    if ($LASTEXITCODE -ne 0) {throw "Vivado failed, exit code $LASTEXITCODE"}
} finally {Pop-Location}
