$ErrorActionPreference = "Stop"

$version = "5.2.1"
$archiveName = "upx-$version-win64.zip"
$expectedSha256 = "eabc6792a347d45e945be7748423e7868fd01b0d2bcaa2f4b1031fd71ff69bda"
$url = "https://github.com/upx/upx/releases/download/v$version/$archiveName"

$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsRoot = Join-Path $projectRoot ".build-tools"
$versionRoot = Join-Path $toolsRoot "upx-$version"
$upxDir = Join-Path $versionRoot "upx-$version-win64"
$upxExe = Join-Path $upxDir "upx.exe"
$archivePath = Join-Path $versionRoot $archiveName

if (Test-Path $upxExe) {
    Write-Host "UPX $version already available: $upxExe"
    exit 0
}

New-Item -ItemType Directory -Force -Path $versionRoot | Out-Null
Write-Host "Downloading UPX $version..."
Invoke-WebRequest -Uri $url -OutFile $archivePath -UseBasicParsing
$actualSha256 = (Get-FileHash -Path $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualSha256 -ne $expectedSha256) {
    Remove-Item $archivePath -Force -ErrorAction SilentlyContinue
    throw "UPX archive SHA-256 mismatch. Expected $expectedSha256, got $actualSha256"
}

Write-Host "Verified UPX archive SHA-256."
Expand-Archive -Path $archivePath -DestinationPath $versionRoot -Force
Remove-Item $archivePath -Force

if (-not (Test-Path $upxExe)) {
    throw "UPX extraction failed: $upxExe was not created."
}

Write-Host "UPX $version ready: $upxExe"
