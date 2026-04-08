param([string]$Message)
Add-Type -AssemblyName System.Windows.Forms
$wshell = New-Object -ComObject wscript.shell

# Copy message to clipboard and paste into the active window
[System.Windows.Forms.Clipboard]::SetText($Message)
Start-Sleep -Milliseconds 200
$wshell.SendKeys("^v")
Start-Sleep -Milliseconds 100
$wshell.SendKeys("{ENTER}")
Write-Output "SENT"
