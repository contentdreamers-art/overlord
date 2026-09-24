$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$source = Join-Path $project 'Source'
$module = Join-Path $source 'soulwoodgame'
New-Item -ItemType Directory -Force -Path $module | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $project 'Config') | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'cpp/SoulwoodGame.Target.cs') $source -Force
Copy-Item (Join-Path $PSScriptRoot 'cpp/SoulwoodGameEditor.Target.cs') $source -Force
Copy-Item (Join-Path $PSScriptRoot 'cpp/soulwoodgame.Build.cs') $module -Force
Copy-Item (Join-Path $PSScriptRoot 'cpp/soulwoodgame.cpp') $module -Force
Copy-Item (Join-Path $PSScriptRoot 'cpp/SoulwoodGameplay.h') $module -Force
Copy-Item (Join-Path $PSScriptRoot 'cpp/SoulwoodGameplay.cpp') $module -Force
Copy-Item (Join-Path $PSScriptRoot 'config/DefaultInput.ini') (Join-Path $project 'Config') -Force
Copy-Item (Join-Path $PSScriptRoot 'config/DefaultEngine.ini') (Join-Path $project 'Config') -Force
$uprojectPath = Join-Path $project 'soulwoodgame.uproject'
$uproject = Get-Content $uprojectPath -Raw | ConvertFrom-Json
$uproject | Add-Member -NotePropertyName Modules -NotePropertyValue @(@{Name='soulwoodgame';Type='Runtime';LoadingPhase='Default'}) -Force
$uproject | ConvertTo-Json -Depth 16 | Set-Content $uprojectPath -Encoding UTF8
Write-Output "Installed original Soulwood module and input configuration into $project"
