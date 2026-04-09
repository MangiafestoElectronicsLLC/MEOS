[CmdletBinding()]
param(
    [switch]$NoAutoBump
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PluginSourceDir = Join-Path $Root "repository.meos"
$PluginAddonXmlPath = Join-Path $PluginSourceDir "addon.xml"
$RepositoryAddonXmlPath = Join-Path $Root "addon.xml"
$ZipsRoot = Join-Path $Root "zips"
$AddonsXmlPath = Join-Path $Root "addons.xml"
$AddonsMd5Path = Join-Path $Root "addons.xml.md5"
$RepositoryZipConveniencePath = Join-Path $Root "repository.meos.zip"

function Get-NextPatchVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Version
    )

    if ($Version -notmatch '^(\d+)\.(\d+)\.(\d+)$') {
        throw "Unsupported version format '$Version'. Expected SemVer patch format like 1.0.0"
    }

    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $patch = [int]$Matches[3] + 1
    return "{0}.{1}.{2}" -f $major, $minor, $patch
}

function Update-AddonVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AddonXmlPath
    )

    [xml]$xmlDoc = Get-Content -Path $AddonXmlPath
    $oldVersion = $xmlDoc.addon.version
    if ([string]::IsNullOrWhiteSpace($oldVersion)) {
        throw "Missing version in $AddonXmlPath"
    }

    $newVersion = Get-NextPatchVersion -Version $oldVersion
    $xmlDoc.addon.version = $newVersion
    $xmlDoc.Save($AddonXmlPath)
    return @{
        OldVersion = $oldVersion
        NewVersion = $newVersion
    }
}

if (-not (Test-Path $PluginAddonXmlPath)) {
    throw "Missing plugin addon.xml at $PluginAddonXmlPath"
}
if (-not (Test-Path $RepositoryAddonXmlPath)) {
    throw "Missing repository addon.xml at $RepositoryAddonXmlPath"
}

[xml]$pluginXml = Get-Content -Path $PluginAddonXmlPath
[xml]$repositoryXml = Get-Content -Path $RepositoryAddonXmlPath

if (-not $NoAutoBump) {
    $pluginBump = Update-AddonVersion -AddonXmlPath $PluginAddonXmlPath
    $repositoryBump = Update-AddonVersion -AddonXmlPath $RepositoryAddonXmlPath

    [xml]$pluginXml = Get-Content -Path $PluginAddonXmlPath
    [xml]$repositoryXml = Get-Content -Path $RepositoryAddonXmlPath
}

$pluginId = $pluginXml.addon.id
$pluginVersion = $pluginXml.addon.version
$repositoryId = $repositoryXml.addon.id
$repositoryVersion = $repositoryXml.addon.version

if ([string]::IsNullOrWhiteSpace($pluginId) -or [string]::IsNullOrWhiteSpace($pluginVersion)) {
    throw "Plugin addon.xml is missing id or version"
}
if ([string]::IsNullOrWhiteSpace($repositoryId) -or [string]::IsNullOrWhiteSpace($repositoryVersion)) {
    throw "Repository addon.xml is missing id or version"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

function New-ZipFromFolder {
    param(
        [Parameter(Mandatory = $true)] [string]$SourceFolder,
        [Parameter(Mandatory = $true)] [string]$DestinationZip
    )

    if (Test-Path $DestinationZip) {
        Remove-Item -Path $DestinationZip -Force
    }

    [System.IO.Compression.ZipFile]::CreateFromDirectory($SourceFolder, $DestinationZip)
}

if (-not (Test-Path $ZipsRoot)) {
    New-Item -ItemType Directory -Path $ZipsRoot | Out-Null
}

$pluginZipDir = Join-Path $ZipsRoot $pluginId
if (-not (Test-Path $pluginZipDir)) {
    New-Item -ItemType Directory -Path $pluginZipDir | Out-Null
}

$pluginZipPath = Join-Path $pluginZipDir ("{0}-{1}.zip" -f $pluginId, $pluginVersion)
$pluginStagingRoot = Join-Path $env:TEMP ("meos-plugin-stage-{0}" -f [guid]::NewGuid().ToString("N"))
$pluginStagingDir = Join-Path $pluginStagingRoot $pluginId
New-Item -ItemType Directory -Path $pluginStagingDir -Force | Out-Null

Copy-Item -Path (Join-Path $PluginSourceDir "*") -Destination $pluginStagingDir -Recurse -Force

New-ZipFromFolder -SourceFolder $pluginStagingRoot -DestinationZip $pluginZipPath
Remove-Item -Path $pluginStagingRoot -Recurse -Force

$addonsXmlContent = @(
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<addons>'
    $pluginXml.addon.OuterXml
    '</addons>'
) -join [Environment]::NewLine

Set-Content -Path $AddonsXmlPath -Value $addonsXmlContent -Encoding UTF8

$md5Hash = (Get-FileHash -Path $AddonsXmlPath -Algorithm MD5).Hash.ToLowerInvariant()
Set-Content -Path $AddonsMd5Path -Value $md5Hash -Encoding ASCII

$repositoryZipPath = Join-Path $Root ("{0}-{1}.zip" -f $repositoryId, $repositoryVersion)
$repositoryStagingRoot = Join-Path $env:TEMP ("meos-repo-stage-{0}" -f [guid]::NewGuid().ToString("N"))
$repositoryStagingDir = Join-Path $repositoryStagingRoot $repositoryId
New-Item -ItemType Directory -Path $repositoryStagingDir -Force | Out-Null

Copy-Item -Path $RepositoryAddonXmlPath -Destination (Join-Path $repositoryStagingDir "addon.xml") -Force
Copy-Item -Path $AddonsXmlPath -Destination (Join-Path $repositoryStagingDir "addons.xml") -Force
Copy-Item -Path $AddonsMd5Path -Destination (Join-Path $repositoryStagingDir "addons.xml.md5") -Force
Copy-Item -Path $ZipsRoot -Destination (Join-Path $repositoryStagingDir "zips") -Recurse -Force

$optionalRepositoryFiles = @("icon.png", "fanart.jpg", "README.md", "LICENSE")
foreach ($fileName in $optionalRepositoryFiles) {
    $sourcePath = Join-Path $Root $fileName
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination (Join-Path $repositoryStagingDir $fileName) -Force
    }
}

New-ZipFromFolder -SourceFolder $repositoryStagingRoot -DestinationZip $repositoryZipPath
Remove-Item -Path $repositoryStagingRoot -Recurse -Force

Copy-Item -Path $repositoryZipPath -Destination $RepositoryZipConveniencePath -Force

Write-Host "Build completed"
if (-not $NoAutoBump) {
    Write-Host "Plugin version: $($pluginBump.OldVersion) -> $($pluginBump.NewVersion)"
    Write-Host "Repository version: $($repositoryBump.OldVersion) -> $($repositoryBump.NewVersion)"
}
else {
    Write-Host "Auto version bump skipped (-NoAutoBump)"
}
Write-Host "Plugin zip: $pluginZipPath"
Write-Host "Repository zip: $repositoryZipPath"
Write-Host "Repository zip (convenience): $RepositoryZipConveniencePath"
Write-Host "Updated: $AddonsXmlPath"
Write-Host "Updated: $AddonsMd5Path"
Write-Host "Repository zip includes: addon.xml, addons.xml, addons.xml.md5, and zips/"
