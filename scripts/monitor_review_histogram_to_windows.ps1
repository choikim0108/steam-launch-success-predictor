param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [int]$PollSeconds = 300
)

$ErrorActionPreference = 'Stop'
Set-Location $Root
$env:PYTHONPATH = 'src'

$LogPath = Join-Path $Root 'data\raw\review_histogram_monitor.log'
$CollectorLogPath = Join-Path $Root 'data\raw\review_histogram_collection_monitor.log'
$CollectorPidPath = Join-Path $Root 'data\raw\review_histogram_collection_monitor.pid'

function Write-MonitorLog {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Encoding UTF8 $LogPath "[$timestamp] $Message"
}

function Get-EligibleTarget {
    $candidates = Import-Csv 'data\interim\game_candidates_2025_2026.csv'
    return @($candidates | Where-Object { $_.label_eligible_90d -eq 'True' }).Count
}

function Get-HistogramStatus {
    $target = Get-EligibleTarget
    $status = if (Test-Path 'data\raw\steam_review_histogram_status.csv') {
        @(Import-Csv 'data\raw\steam_review_histogram_status.csv')
    } else {
        @()
    }
    return [pscustomobject]@{
        Target = $target
        Rows = $status.Count
        SuccessRows = @($status | Where-Object { $_.histogram_success -eq 'True' }).Count
        ErrorRows = @($status | Where-Object { $_.histogram_success -ne 'True' }).Count
    }
}

function Test-CollectorAlive {
    if (!(Test-Path $CollectorPidPath)) {
        return @((Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*steam_success.collect.review_histogram*' })).Count -gt 0
    }
    $value = Get-Content $CollectorPidPath -ErrorAction SilentlyContinue
    if ([string]::IsNullOrWhiteSpace($value)) {
        return @((Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*steam_success.collect.review_histogram*' })).Count -gt 0
    }
    if ([bool](Get-Process -Id ([int]$value) -ErrorAction SilentlyContinue)) {
        return $true
    }
    return @((Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*steam_success.collect.review_histogram*' })).Count -gt 0
}

function Remove-HistogramFailuresFromStatus {
    $statusPath = 'data\raw\steam_review_histogram_status.csv'
    if (!(Test-Path $statusPath)) {
        return 0
    }
    $status = @(Import-Csv $statusPath)
    $failed = @($status | Where-Object { $_.histogram_success -ne 'True' })
    if ($failed.Count -eq 0) {
        return 0
    }
    $backupPath = "data\raw\steam_review_histogram_status.monitor_before_retry_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
    Copy-Item $statusPath $backupPath
    @($status | Where-Object { $_.histogram_success -eq 'True' }) |
        Export-Csv $statusPath -NoTypeInformation -Encoding UTF8
    Write-MonitorLog "removed failed histogram status rows count=$($failed.Count) backup=$backupPath"
    return $failed.Count
}

function Start-HistogramCollector {
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Encoding UTF8 $CollectorLogPath "`n--- monitor start $timestamp ---"
    $command = "`$env:PYTHONPATH='src'; python -u -m steam_success.collect.review_histogram --input-csv data/interim/game_candidates_2025_2026.csv --only-label-eligible-90d --flush-every 100 --sleep-seconds 0.5 --max-retries 5 2>&1 | Tee-Object -FilePath '$CollectorLogPath' -Append"
    $proc = Start-Process -FilePath powershell -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $command) -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    $proc.Id | Set-Content -Encoding ASCII $CollectorPidPath
    Write-MonitorLog "started histogram collector pid=$($proc.Id)"
}

Write-MonitorLog "monitor started root=$Root poll_seconds=$PollSeconds"

while ($true) {
    $status = Get-HistogramStatus
    $alive = Test-CollectorAlive
    Write-MonitorLog "status histogram=$($status.Rows)/$($status.Target) success=$($status.SuccessRows) errors=$($status.ErrorRows) collector_alive=$alive"

    if ($status.Rows -ge $status.Target -and $status.ErrorRows -eq 0) {
        break
    }

    if (!$alive) {
        if ($status.ErrorRows -gt 0) {
            Remove-HistogramFailuresFromStatus | Out-Null
        }
        Start-HistogramCollector
    }

    Start-Sleep -Seconds $PollSeconds
}

Write-MonitorLog 'running review_windows'
python -u -m steam_success.preprocess.review_windows 2>&1 |
    Tee-Object -FilePath $LogPath -Append

Write-MonitorLog 'monitor complete'
