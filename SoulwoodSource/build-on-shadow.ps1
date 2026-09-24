$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$engine = Get-ChildItem 'C:\Program Files\Epic Games' -Directory |
    Where-Object { $_.Name -like 'UE_*' } |
    Sort-Object Name -Descending |
    Select-Object -First 1
if (-not $engine) { throw 'Unreal Engine installation was not found.' }
$build = Join-Path $engine.FullName 'Engine\Build\BatchFiles\Build.bat'
if (-not (Test-Path $build)) { throw "Build.bat was not found at $build" }
$uproject = Join-Path $project 'soulwoodgame.uproject'
$log = Join-Path $project 'soulwood-build.log'
Write-Output "Building $uproject with $build"
& $build SoulwoodGameEditor Win64 Development "-Project=$uproject" -WaitMutex -NoHotReload 2>&1 |
    Tee-Object -FilePath $log
if ($LASTEXITCODE -ne 0) { throw "Build failed with exit code $LASTEXITCODE. Log: $log" }
Write-Output "SOULWOOD_BUILD_SUCCEEDED $log"
