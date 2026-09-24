$ErrorActionPreference = 'Stop'
$package = Get-AppxPackage BlenderFoundation.Blender
if (-not $package) { throw 'Blender 5.x is not installed on this workstation' }
$executable = Get-ChildItem -LiteralPath $package.InstallLocation -Filter blender.exe -Recurse -File | Select-Object -First 1
if (-not $executable) { throw 'Could not find blender.exe in the installed package' }
$script = Join-Path $PSScriptRoot 'blender/make_enhanced_forest.py'
& $executable.FullName -b -t 4 -P $script
if ($LASTEXITCODE -ne 0) { throw "Blender exited with code $LASTEXITCODE" }
Write-Output 'SOULWOOD_ENHANCED_BLENDER_SUCCEEDED'
