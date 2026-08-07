$ErrorActionPreference = "Stop"

$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$name = "ResearchOSLocalAPI"

if (Get-ItemProperty -Path $runKey -Name $name -ErrorAction SilentlyContinue) {
  Remove-ItemProperty -Path $runKey -Name $name
  Write-Host "Research OS Local API autostart disabled."
} else {
  Write-Host "Research OS Local API autostart is already disabled."
}
