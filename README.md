General Folders
-Games
-Programs
-Apps
-Music
-Usb Flash Installer
-More Stuff


irm 'https://github.com/Dim03Real/General-Folder/releases/download/Manager/ManagerInstall.zip' -OutFile "$env:USERPROFILE\Downloads\ManagerInstall.zip"; Expand-Archive "$env:USERPROFILE\Downloads\ManagerInstall.zip" "$env:USERPROFILE\Downloads\ManagerInstall" -Force; Start-Process "$env:USERPROFILE\Downloads\ManagerInstall"; Stop-Process -Id $PID


use powershell cause it can be auto update instead installing
