# run_jarvis.ps1

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
chcp 65001 > $null

Set-Location $PSScriptRoot
Clear-Host

Write-Host ""
Write-Host "様様様様様様様様様様様様様様様様様様様様様様様" -ForegroundColor Cyan
Write-Host "?? JARVIS AI PLATFORM" -ForegroundColor Cyan
Write-Host "様様様様様様様様様様様様様様様様様様様様様様様" -ForegroundColor Cyan
Write-Host ""

python launcher.py