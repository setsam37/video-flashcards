function Get-RecallPython {
    param([string]$AppRoot, $Runtime)
    if ($Runtime -and $Runtime.python) { return $Runtime.python }
    $localPython = Join-Path $AppRoot '.venv/Scripts/python.exe'
    if (Test-Path -LiteralPath $localPython -PathType Leaf) { return (Resolve-Path -LiteralPath $localPython).Path }
    return (Get-Command python -ErrorAction Stop).Source
}
