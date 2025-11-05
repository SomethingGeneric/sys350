# Make a linked clone
$source = Read-Host -Prompt "VM to clone: "
$destname = Read-Host -Prompt "New VM Name: "
$switchname = Read-Host -Prompt "VMSwitch to use: "

# Get VM disk from name (found in `Get-Help Get-VHD -examples`)
$target_disk = Get-VM -VMName $source | Select-Object VMId | Get-VHD

Write-Host "Cloning $source with disk path $target_disk.Path"

# make new diff disk from source path (Found in `Get-Help New-VHD -examples`)
$new_disk = New-VHD -ParentPath $target_disk.Path -Path "C:\ProgramData\Microsoft\Windows\Virtual Hard Disks\$destname.vhdx" -Differencing

# Make new VM (from : https://learn.microsoft.com/en-us/powershell/module/hyper-v/new-vm?view=windowsserver2025-ps)

$VM = @{
    Name = $destname
    MemoryStartupBytes = 2147483648
    Generation = 2
    VHDPath = $new_disk.Path
    BootDevice = "VHD"
    Path = "C:\Virtual Machines\$VMName"
    SwitchName = $switchname
 }

New-VM @VM

# Gemini gave me this when I google searched
Set-VMFirmware -VMName $destname -EnableSecureBoot Off

Start-VM $destname