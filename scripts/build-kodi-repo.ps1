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
$SingleInstallZipPath = Join-Path $Root "MEOS_ADDON.zip"
$SingleInstallZipModernPath = Join-Path $Root "MEOS_ADDON_K21.zip"
$KodiInstallDir = Join-Path $Root "KodiInstall"

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

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function New-ZipFromFolder {
    param(
        [Parameter(Mandatory = $true)] [string]$SourceFolder,
        [Parameter(Mandatory = $true)] [string]$DestinationZip
    )

    if (Test-Path $DestinationZip) {
        Remove-Item -Path $DestinationZip -Force
    }

    $destinationDir = Split-Path -Path $DestinationZip -Parent
    if ($destinationDir -and -not (Test-Path $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir | Out-Null
    }

    $fileStream = [System.IO.File]::Open($DestinationZip, [System.IO.FileMode]::Create)
    try {
        $archive = New-Object System.IO.Compression.ZipArchive($fileStream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
        try {
            $sourceRoot = (Resolve-Path $SourceFolder).Path
            $prefixLength = $sourceRoot.Length
            if (-not $sourceRoot.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
                $prefixLength += 1
            }

            Get-ChildItem -Path $sourceRoot -Recurse -File | ForEach-Object {
                $fullPath = $_.FullName
                $relativePath = $fullPath.Substring($prefixLength)
                $entryName = $relativePath -replace '\\', '/'
                $entry = $archive.CreateEntry($entryName, [System.IO.Compression.CompressionLevel]::Optimal)

                $entryStream = $entry.Open()
                try {
                    $inputFileStream = [System.IO.File]::OpenRead($fullPath)
                    try {
                        $inputFileStream.CopyTo($entryStream)
                    }
                    finally {
                        $inputFileStream.Dispose()
                    }
                }
                finally {
                    $entryStream.Dispose()
                }
            }
        }
        finally {
            $archive.Dispose()
        }
    }
    finally {
        $fileStream.Dispose()
    }
}

function Set-PluginPythonDependencyVersion {
    param(
        [Parameter(Mandatory = $true)] [string]$AddonXmlPath,
        [Parameter(Mandatory = $true)] [string]$PythonDependencyVersion
    )

    [xml]$xmlDoc = Get-Content -Path $AddonXmlPath
    $requiresNode = $xmlDoc.addon.requires
    if (-not $requiresNode) {
        throw "Missing <requires> in $AddonXmlPath"
    }

    $importNode = $requiresNode.import | Where-Object { $_.addon -eq "xbmc.python" } | Select-Object -First 1
    if (-not $importNode) {
        throw "Missing xbmc.python import in $AddonXmlPath"
    }

    $importNode.version = $PythonDependencyVersion
    $xmlDoc.Save($AddonXmlPath)
}

if (-not (Test-Path $ZipsRoot)) {
    New-Item -ItemType Directory -Path $ZipsRoot | Out-Null
}

$pluginZipDir = Join-Path $ZipsRoot $pluginId
if (-not (Test-Path $pluginZipDir)) {
    New-Item -ItemType Directory -Path $pluginZipDir | Out-Null
}

$legacyPluginZipPath = Join-Path $ZipsRoot ("{0}.zip" -f $pluginId)
if (Test-Path $legacyPluginZipPath) {
    Remove-Item -Path $legacyPluginZipPath -Force
}

$k18PluginZipPath = Join-Path $pluginZipDir ("{0}-{1}-k18.zip" -f $pluginId, $pluginVersion)
$k21PluginZipPath = Join-Path $pluginZipDir ("{0}-{1}.zip" -f $pluginId, $pluginVersion)

$profileDefinitions = @(
    @{
        Name                    = "k18"
        PythonDependencyVersion = "2.25.0"
        ProfileZipPath          = $k18PluginZipPath
        InstallZipPath          = $SingleInstallZipPath
    },
    @{
        Name                    = "k21"
        PythonDependencyVersion = "3.0.0"
        ProfileZipPath          = $k21PluginZipPath
        InstallZipPath          = $SingleInstallZipModernPath
    }
)

foreach ($profile in $profileDefinitions) {
    $pluginStagingRoot = Join-Path $env:TEMP ("meos-plugin-{0}-stage-{1}" -f $profile.Name, [guid]::NewGuid().ToString("N"))
    $pluginStagingDir = Join-Path $pluginStagingRoot $pluginId
    New-Item -ItemType Directory -Path $pluginStagingDir -Force | Out-Null

    Copy-Item -Path (Join-Path $PluginSourceDir "*") -Destination $pluginStagingDir -Recurse -Force

    $stagedAddonXmlPath = Join-Path $pluginStagingDir "addon.xml"
    Set-PluginPythonDependencyVersion -AddonXmlPath $stagedAddonXmlPath -PythonDependencyVersion $profile.PythonDependencyVersion

    New-ZipFromFolder -SourceFolder $pluginStagingRoot -DestinationZip $profile.ProfileZipPath
    Copy-Item -Path $profile.ProfileZipPath -Destination $profile.InstallZipPath -Force

    Remove-Item -Path $pluginStagingRoot -Recurse -Force
}

$addonsXmlContent = @(
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<addons>'
    $pluginXml.addon.OuterXml
    '</addons>'
) -join [Environment]::NewLine

[System.IO.File]::WriteAllText($AddonsXmlPath, $addonsXmlContent, (New-Object System.Text.UTF8Encoding($false)))

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

if (-not (Test-Path $KodiInstallDir)) {
    New-Item -ItemType Directory -Path $KodiInstallDir | Out-Null
}

Copy-Item -Path $SingleInstallZipPath -Destination (Join-Path $KodiInstallDir "MEOS_ADDON.zip") -Force
Copy-Item -Path $SingleInstallZipModernPath -Destination (Join-Path $KodiInstallDir "MEOS_ADDON_K21.zip") -Force
Copy-Item -Path $RepositoryZipConveniencePath -Destination (Join-Path $KodiInstallDir "repository.meos.zip") -Force

Write-Host "Build completed"
if (-not $NoAutoBump) {
    Write-Host "Plugin version: $($pluginBump.OldVersion) -> $($pluginBump.NewVersion)"
    Write-Host "Repository version: $($repositoryBump.OldVersion) -> $($repositoryBump.NewVersion)"
}
else {
    Write-Host "Auto version bump skipped (-NoAutoBump)"
}
Write-Host "Plugin zip (Kodi 18): $k18PluginZipPath"
Write-Host "Plugin zip (Kodi 21/22): $k21PluginZipPath"
Write-Host "Single install zip (Kodi 18): $SingleInstallZipPath"
Write-Host "Single install zip (Kodi 21/22): $SingleInstallZipModernPath"
Write-Host "Repository zip: $repositoryZipPath"
Write-Host "Repository zip (convenience): $RepositoryZipConveniencePath"
Write-Host "KodiInstall folder: $KodiInstallDir"
Write-Host "Updated: $AddonsXmlPath"
Write-Host "Updated: $AddonsMd5Path"
Write-Host "Repository zip includes: addon.xml, addons.xml, addons.xml.md5, and zips/"
