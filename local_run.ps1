# Daily local run on Jon's PC: Google Flights works far better from a home
# connection than from GitHub's servers. Scheduled by Windows Task Scheduler.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$log = Join-Path $PSScriptRoot "local_run.log"
"=== $(Get-Date -Format s) ===" | Out-File $log -Append
git pull --rebase --autostash origin main *>> $log
& .\.venv\Scripts\python.exe -u -m tracker.run --dest international --google-only --samples 6 --tag local *>> $log
git add data/ *>> $log
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "Local fare log $(Get-Date -Format yyyy-MM-dd)" *>> $log
    git pull --rebase origin main *>> $log
    git push origin main *>> $log
}
