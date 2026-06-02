param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [int]$PollSeconds = 300
)

$ErrorActionPreference = 'Stop'
Set-Location $Root
$env:PYTHONPATH = 'src'

$LogPath = Join-Path $Root 'data\raw\data_collection_orchestrator.log'
$AppdetailsPidPath = Join-Path $Root 'data\raw\appdetails_collection.pid'
$AppdetailsLogPath = Join-Path $Root 'data\raw\appdetails_collection.log'
$HistogramPidPath = Join-Path $Root 'data\raw\review_histogram_collection.pid'
$HistogramLogPath = Join-Path $Root 'data\raw\review_histogram_collection.log'

function Write-OrchestratorLog {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Encoding UTF8 $LogPath "[$timestamp] $Message"
}

function Get-TargetCount {
    return @((Import-Csv 'data\interim\search_release_window_appids.csv')).Count
}

function Get-DataStatus {
    $target = Get-TargetCount
    $details = if (Test-Path 'data\raw\steam_appdetails.csv') { @(Import-Csv 'data\raw\steam_appdetails.csv') } else { @() }
    $summaries = if (Test-Path 'data\raw\steam_review_summaries.csv') { @(Import-Csv 'data\raw\steam_review_summaries.csv') } else { @() }
    return [pscustomobject]@{
        Target = $target
        DetailsRows = $details.Count
        DetailSuccessRows = @($details | Where-Object { $_.detail_success -eq 'True' }).Count
        DetailErrorRows = @($details | Where-Object { -not [string]::IsNullOrWhiteSpace($_.detail_error) }).Count
        ReviewRows = $summaries.Count
        ReviewErrorRows = @($summaries | Where-Object { $_.review_success -ne 'True' }).Count
    }
}

function Test-ProcessAlive {
    param([string]$PidPath)
    if (!(Test-Path $PidPath)) {
        return $false
    }
    $value = Get-Content $PidPath -ErrorAction SilentlyContinue
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $false
    }
    return [bool](Get-Process -Id ([int]$value) -ErrorAction SilentlyContinue)
}

function Start-AppdetailsCollector {
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Encoding UTF8 $AppdetailsLogPath "`n--- orchestrator restart $timestamp ---"
    $command = "`$env:PYTHONPATH='src'; python -u -m steam_success.collect.appdetails_for_appids --input-csv data/interim/search_release_window_appids.csv --flush-every 100 --sleep-seconds 1.0 --max-retries 5 2>&1 | Tee-Object -FilePath '$AppdetailsLogPath' -Append"
    $proc = Start-Process -FilePath powershell -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $command) -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    $proc.Id | Set-Content -Encoding ASCII $AppdetailsPidPath
    Write-OrchestratorLog "started appdetails collector pid=$($proc.Id)"
}

function Invoke-AppdetailsRetryPass {
    Write-OrchestratorLog 'starting final appdetails retry pass'
    python -u -m steam_success.collect.appdetails_for_appids --input-csv data/interim/search_release_window_appids.csv --flush-every 100 --sleep-seconds 1.0 --max-retries 5 2>&1 |
        Tee-Object -FilePath $AppdetailsLogPath -Append
    $status = Get-DataStatus
    Write-OrchestratorLog "retry pass done details=$($status.DetailsRows)/$($status.Target) detail_errors=$($status.DetailErrorRows) review_errors=$($status.ReviewErrorRows)"
}

Write-OrchestratorLog "orchestrator started root=$Root poll_seconds=$PollSeconds"

while ($true) {
    $status = Get-DataStatus
    Write-OrchestratorLog "status details=$($status.DetailsRows)/$($status.Target) reviews=$($status.ReviewRows)/$($status.Target) detail_errors=$($status.DetailErrorRows) review_errors=$($status.ReviewErrorRows)"

    if ($status.DetailsRows -ge $status.Target -and $status.ReviewRows -ge $status.Target) {
        break
    }

    if (!(Test-ProcessAlive $AppdetailsPidPath)) {
        Write-OrchestratorLog 'appdetails collector not alive before completion'
        Start-AppdetailsCollector
    }

    Start-Sleep -Seconds $PollSeconds
}

for ($attempt = 1; $attempt -le 5; $attempt++) {
    $status = Get-DataStatus
    if ($status.DetailErrorRows -eq 0 -and $status.ReviewErrorRows -eq 0) {
        break
    }
    Write-OrchestratorLog "retry attempt=$attempt detail_errors=$($status.DetailErrorRows) review_errors=$($status.ReviewErrorRows)"
    Invoke-AppdetailsRetryPass
    Start-Sleep -Seconds 60
}

$status = Get-DataStatus
if ($status.DetailsRows -lt $status.Target -or $status.ReviewRows -lt $status.Target -or $status.DetailErrorRows -ne 0 -or $status.ReviewErrorRows -ne 0) {
    Write-OrchestratorLog "stopping before downstream incomplete details=$($status.DetailsRows)/$($status.Target) reviews=$($status.ReviewRows)/$($status.Target) detail_errors=$($status.DetailErrorRows) review_errors=$($status.ReviewErrorRows)"
    exit 2
}

Write-OrchestratorLog 'running candidate_filter'
python -u -m steam_success.preprocess.candidate_filter --start-year 2025 --end-year 2026 2>&1 |
    Tee-Object -FilePath $LogPath -Append

Write-OrchestratorLog 'running review_histogram for label_eligible_90d candidates'
$histCommand = "`$env:PYTHONPATH='src'; python -u -m steam_success.collect.review_histogram --input-csv data/interim/game_candidates_2025_2026.csv --only-label-eligible-90d --flush-every 100 --sleep-seconds 0.5 --max-retries 5 2>&1 | Tee-Object -FilePath '$HistogramLogPath' -Append"
$histProc = Start-Process -FilePath powershell -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $histCommand) -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$histProc.Id | Set-Content -Encoding ASCII $HistogramPidPath
Write-OrchestratorLog "started review_histogram collector pid=$($histProc.Id)"
Wait-Process -Id $histProc.Id
Write-OrchestratorLog 'review_histogram collector finished'

Write-OrchestratorLog 'running review_windows'
python -u -m steam_success.preprocess.review_windows 2>&1 |
    Tee-Object -FilePath $LogPath -Append

Write-OrchestratorLog 'orchestrator complete'
