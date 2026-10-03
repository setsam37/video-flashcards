$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $appRoot 'data/processes.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Host 'No recorded Recall processes.'; return }
$runtimePath = Join-Path $PSScriptRoot 'runtime.json'
$runtime = if (Test-Path -LiteralPath $runtimePath) { Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json } else { $null }
. (Join-Path $PSScriptRoot 'runtime.ps1')
$pythonExe = Get-RecallPython -AppRoot $appRoot -Runtime $runtime
& $pythonExe (Join-Path $PSScriptRoot 'process_info.py') stop --record $statePath
if ($LASTEXITCODE -ne 0) { throw 'An app process could not be safely stopped. Its process record is preserved.' }
