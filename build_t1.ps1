param(
    [string]$PythonExe = "python",
    [string]$YosysExe = "yosys",
    [string]$NextpnrExe = "nextpnr-ice40",
    [string]$IcepackExe = "icepack",
    [switch]$SkipSimulation
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$build = Join-Path $root "build"
$rtl = Join-Path $root "rtl\fir_audio_top_t1.v"
$pcf = Join-Path $root "rtl\fir_audio_top_hackster.pcf"
$json = Join-Path $build "t1.json"
$asc = Join-Path $build "t1.asc"
$bin = Join-Path $build "t1_fir_audio.bin"

New-Item -ItemType Directory -Force -Path $build | Out-Null

function Invoke-LoggedTool {
    param(
        [Parameter(Mandatory=$true)][string]$Executable,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [Parameter(Mandatory=$true)][string]$LogPath
    )
    & $Executable @Arguments 2>&1 | Tee-Object -FilePath $LogPath
    if ($LASTEXITCODE -ne 0) {
        throw "$Executable failed with exit code $LASTEXITCODE. See $LogPath"
    }
}

if (-not $SkipSimulation) {
    $simArgs = @((Join-Path $root "tb\run_tests.py"))
    Invoke-LoggedTool -Executable $PythonExe -Arguments $simArgs -LogPath (Join-Path $build "simulation.log")
}

$yosysScript = "read_verilog -sv `"$rtl`"; synth_ice40 -top fir_audio_top -json `"$json`"; stat; check"
$yosysArgs = @("-p", $yosysScript)
Invoke-LoggedTool -Executable $YosysExe -Arguments $yosysArgs -LogPath (Join-Path $build "yosys.log")

$pnrArgs = @(
    "--up5k", "--package", "sg48", "--json", $json,
    "--pcf", $pcf, "--freq", "10", "--asc", $asc
)
Invoke-LoggedTool -Executable $NextpnrExe -Arguments $pnrArgs -LogPath (Join-Path $build "nextpnr.log")

$packArgs = @($asc, $bin)
Invoke-LoggedTool -Executable $IcepackExe -Arguments $packArgs -LogPath (Join-Path $build "icepack.log")

Write-Output "Bitstream created: $bin"
Write-Output "Programming is intentionally a separate operator step. Use the official Challenge 3 FPGA Makefile after reviewing the generated artifact."
