# Creates a weekly Windows Task that runs main.py every Monday at 10:00.
# Run once in PowerShell:  powershell -ExecutionPolicy Bypass -File setup_schedule.ps1
# To remove later:         schtasks /Delete /TN "WeeklyJobApplier" /F

$ProjectDir = $PSScriptRoot
$Python = (Get-Command python).Source
$TaskName = "WeeklyJobApplier"

$Action = "`"$Python`" `"$ProjectDir\main.py`""
schtasks /Create /TN $TaskName /TR $Action /SC WEEKLY /D MON /ST 10:00 /F
Write-Host "Scheduled '$TaskName' every Monday 10:00. The PC must be on and logged in at that time."
