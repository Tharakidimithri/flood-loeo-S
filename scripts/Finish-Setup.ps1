param([string]$WaitFor = '')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
$statusFile = Join-Path (Get-Location) 'reports\setup-status.txt'
Start-Transcript -Path reports/setup.log -Append
try {
    'Waiting for downloads already in progress' | Set-Content $statusFile
    foreach ($taskProcess in ($WaitFor -split ',' | Where-Object { $_ })) {
        $proc = Get-Process -Id $taskProcess -ErrorAction SilentlyContinue
        if ($proc) { $proc.WaitForExit() }
    }
    'Installing GPU PyTorch' | Set-Content $statusFile
    & $python -m pip install torch torchvision --find-links .downloads --index-url https://download.pytorch.org/whl/cu128 --timeout 120 --retries 5 --resume-retries 10
    if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed. See setup.log.' }
    'Installing project dependencies' | Set-Content $statusFile
    & $python -m pip install -r requirements.txt --timeout 120 --retries 5 --resume-retries 10
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. See setup.log.' }
    & $python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency check failed.' }
    & $python scripts/verify_environment.py
    if ($LASTEXITCODE -ne 0) { throw 'Environment or GPU verification failed.' }
    & $python -m pip freeze | Set-Content requirements-lock.txt
    'Running GPU memory benchmark' | Set-Content $statusFile
    & $python memory_test.py
    if ($LASTEXITCODE -ne 0) { throw 'Benchmark failed; inspect reports/memory_test.json.' }
    'COMPLETE: dependencies installed, GPU verified, benchmark saved in reports/memory_test.csv' | Set-Content $statusFile
} catch {
    ('FAILED: ' + $_.Exception.Message) | Set-Content $statusFile
    Write-Error $_ -ErrorAction Continue
} finally {
    Stop-Transcript
}

