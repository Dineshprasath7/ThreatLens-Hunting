param(
    [ValidateSet('All', 'Train', 'Test', 'Serve', 'Demo')]
    [string]$Mode = 'All',
    [switch]$NoServe
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
Push-Location $projectRoot
try {
    if (-not (Test-Path $venvPython)) {
        Write-Host 'Creating .venv...'
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python virtual environment.' }
    }

    & $venvPython -c 'import flask, pandas, scipy, sklearn, joblib'
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Installing requirements...'
        & $venvPython -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    }

    function Invoke-Python([string[]]$Arguments) {
        Write-Host ('> python ' + ($Arguments -join ' ')) -ForegroundColor Cyan
        & $venvPython @Arguments
        if ($LASTEXITCODE -ne 0) { throw ('Step failed: python ' + ($Arguments -join ' ')) }
    }

    if ($Mode -eq 'All') {
        New-Item -ItemType Directory -Force -Path output | Out-Null
        Invoke-Python -Arguments @('-m', 'src.preprocess', '--input', 'data/KDDTrain+.arff', '--output', 'output/arff_converted.csv')
    }
    if ($Mode -in @('All', 'Train')) {
        Invoke-Python -Arguments @('-m', 'src.train')
    }
    if ($Mode -in @('All', 'Test')) {
        Invoke-Python -Arguments @('-m', 'unittest', 'discover', '-s', 'tests', '-v')
    }
    if ($Mode -in @('All', 'Demo')) {
        foreach ($sample in @('normal', 'dos', 'probe', 'r2l', 'u2r')) {
            Write-Host "Ground-truth example: $sample" -ForegroundColor Yellow
            Invoke-Python -Arguments @('-m', 'src.predict', "examples/$sample.json")
        }
    }
    if ($Mode -eq 'Serve' -or ($Mode -eq 'All' -and -not $NoServe)) {
        $listener = [System.Net.Sockets.TcpClient]::new()
        try {
            $connection = $listener.BeginConnect('127.0.0.1', 5000, $null, $null)
            if ($connection.AsyncWaitHandle.WaitOne(300)) {
                try {
                    $listener.EndConnect($connection)
                    throw 'Port 5000 is already in use. Stop the earlier Flask terminal with Ctrl+C, then run this script again.'
                }
                catch [System.Net.Sockets.SocketException] { }
            }
        }
        finally { $listener.Dispose() }
        Write-Host 'API running at http://127.0.0.1:5000 (Ctrl+C to stop).' -ForegroundColor Green
        Invoke-Python -Arguments @('-m', 'src.deploy')
    }
    elseif ($Mode -eq 'All') {
        Write-Host 'All steps passed. API launch skipped with -NoServe.' -ForegroundColor Green
    }
}
finally {
    Pop-Location
}
