param([switch]$Dev,[switch]$Build)
$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
$runtimePath = Join-Path $PSScriptRoot 'runtime.json'
$runtime = if (Test-Path -LiteralPath $runtimePath) { Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json } else { $null }
$pythonExe = if ($runtime) { $runtime.python } else { (Get-Command python).Source }
$nodeExe = if ($runtime) { $runtime.node } else { (Get-Command node).Source }
$dataPath = Join-Path $appRoot 'data'
$logsPath = Join-Path $dataPath 'logs'
New-Item -ItemType Directory -Force -Path $logsPath | Out-Null
$statePath = Join-Path $dataPath 'processes.json'
if (Test-Path -LiteralPath $statePath) { throw 'An app process record exists. Run scripts/stop.ps1 before restarting.' }
$env:PYTHONPATH = Join-Path $appRoot 'backend'
$nodeOptions = @()
if ($runtime -and $runtime.node_import) { $nodeOptions += @('--import', ([Uri]([IO.Path]::GetFullPath($runtime.node_import))).AbsoluteUri) }
if ($Build -or (-not $Dev -and -not (Test-Path -LiteralPath (Join-Path $appRoot 'web/dist/index.html')))) {
    Push-Location (Join-Path $appRoot 'web')
    try {
        & $nodeExe './node_modules/typescript/bin/tsc' -b
        if ($LASTEXITCODE -ne 0) { throw 'TypeScript build failed.' }
        & $nodeExe @nodeOptions './node_modules/vite/bin/vite.js' build
        if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
    } finally { Pop-Location }
}
$records = @()
function Start-Recorded($role, $executable, $arguments, $workingDirectory) {
    $quotedArgs = $arguments | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }
    $process = Start-Process -FilePath $executable -ArgumentList $quotedArgs -WorkingDirectory $workingDirectory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logsPath "$role.out.log") -RedirectStandardError (Join-Path $logsPath "$role.err.log")
    $items = & $pythonExe (Join-Path $PSScriptRoot 'process_info.py') inspect --pid $process.Id --role $role
    if ($LASTEXITCODE -ne 0) { Stop-Process -Id $process.Id -ErrorAction SilentlyContinue; throw "$role could not be recorded. See data/logs." }
    $script:records += @($items | ConvertFrom-Json)
    $script:records | ConvertTo-Json -AsArray | Set-Content -LiteralPath $statePath -Encoding utf8
}
try {
    Start-Recorded 'api' $pythonExe @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000') $appRoot
    Start-Recorded 'worker' $pythonExe @('-m','app.worker') $appRoot
    if ($Dev) { Start-Recorded 'web' $nodeExe ($nodeOptions + @((Join-Path $appRoot 'web/node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port','5173')) (Join-Path $appRoot 'web') }
    $healthy = $false
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        try { $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 1; $healthy = $health.status -eq 'ok'; if ($healthy) { break } } catch {}
        Start-Sleep -Milliseconds 300
    }
    if (-not $healthy) { throw 'The API did not become ready. See data/logs.' }
    foreach ($record in $records) { if (-not (Get-Process -Id $record.id -ErrorAction SilentlyContinue)) { throw "$($record.role) exited. See data/logs." } }
    Write-Host ('Recall is running: ' + $(if ($Dev) {'http://127.0.0.1:5173'} else {'http://127.0.0.1:8000'}))
} catch {
    & (Join-Path $PSScriptRoot 'stop.ps1')
    throw
}
