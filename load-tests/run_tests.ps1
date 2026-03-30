$ErrorActionPreference = "Stop"

$vus = @(50, 100, 200, 500)
$outDir = "results"

if (!(Test-Path -Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

Write-Host "Starting k6 load tests..."

foreach ($vu in $vus) {
    Write-Host "Running load test with $vu VUs..."
    $env:VUS = $vu
    $outFile = "$outDir\results_${vu}vu.txt"
    # Execute k6 and redirect output to a text file
    k6 run k6_dispatcher_test.js > $outFile 2>&1
    Write-Host "Saved results to $outFile"
}

Write-Host "All load tests completed!"
