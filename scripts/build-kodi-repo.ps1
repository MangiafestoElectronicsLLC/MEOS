[CmdletBinding()]
param(
    [switch]$NoAutoBump
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PluginSourceDir = Join-Path $Root "repository.meos"
$PluginAddonXmlPath = Join-Path $PluginSourceDir "addon.xml"
$HubSourceDir = Join-Path $Root "plugin.video.meoshub"
$HubAddonXmlPath = Join-Path $HubSourceDir "addon.xml"
$RepositoryAddonXmlPath = Join-Path $Root "addon.xml"
$ZipsRoot = Join-Path $Root "zips"
$AddonsXmlPath = Join-Path $Root "addons.xml"
$AddonsMd5Path = Join-Path $Root "addons.xml.md5"
# Kodi 18.7 (Leia) gets its own feed: same add-ons, but declaring xbmc.python 2.x.
$ZipsK18Root = Join-Path $Root "zips-k18"
$AddonsK18XmlPath = Join-Path $Root "addons-k18.xml"
$AddonsK18Md5Path = Join-Path $Root "addons-k18.xml.md5"
$RepositoryZipConveniencePath = Join-Path $Root "repository.meos.zip"
$SingleInstallZipPath = Join-Path $Root "MEOS_ADDON_K18.zip"
$SingleInstallZipModernPath = Join-Path $Root "MEOS_ADDON_K20PLUS.zip"
$HubSingleInstallZipPath = Join-Path $Root "MEOS_HUB_K18.zip"
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
if (-not (Test-Path $HubAddonXmlPath)) {
    throw "Missing hub addon.xml at $HubAddonXmlPath"
}

@(
    (Join-Path $Root "MEOS_ADDON.zip"),
    (Join-Path $Root "MEOS_ADDON_K21.zip")
) | ForEach-Object {
    if (Test-Path $_) {
        Remove-Item -Path $_ -Force
    }
}

[xml]$pluginXml = Get-Content -Path $PluginAddonXmlPath
[xml]$hubXml = Get-Content -Path $HubAddonXmlPath
[xml]$repositoryXml = Get-Content -Path $RepositoryAddonXmlPath

if (-not $NoAutoBump) {
    $pluginBump = Update-AddonVersion -AddonXmlPath $PluginAddonXmlPath
    $hubBump = Update-AddonVersion -AddonXmlPath $HubAddonXmlPath
    $repositoryBump = Update-AddonVersion -AddonXmlPath $RepositoryAddonXmlPath

    [xml]$pluginXml = Get-Content -Path $PluginAddonXmlPath
    [xml]$hubXml = Get-Content -Path $HubAddonXmlPath
    [xml]$repositoryXml = Get-Content -Path $RepositoryAddonXmlPath
}

$pluginId = $pluginXml.addon.id
$pluginVersion = $pluginXml.addon.version
$hubId = $hubXml.addon.id
$hubVersion = $hubXml.addon.version
$repositoryId = $repositoryXml.addon.id
$repositoryVersion = $repositoryXml.addon.version

# Keep repository root clean: only current generated versioned artifacts.
Get-ChildItem -Path $Root -Filter "repository.meos-*.zip" -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $Root -Filter "addons-*.xml" -File -ErrorAction SilentlyContinue |
Where-Object { $_.Name -ne "addons-k18.xml" } |
Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $Root -Filter "addons-*.xml.md5" -File -ErrorAction SilentlyContinue |
Where-Object { $_.Name -ne "addons-k18.xml.md5" } |
Remove-Item -Force -ErrorAction SilentlyContinue

if ([string]::IsNullOrWhiteSpace($pluginId) -or [string]::IsNullOrWhiteSpace($pluginVersion)) {
    throw "Plugin addon.xml is missing id or version"
}
if ([string]::IsNullOrWhiteSpace($hubId) -or [string]::IsNullOrWhiteSpace($hubVersion)) {
    throw "Hub addon.xml is missing id or version"
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

function Set-RepositoryFeedUrls {
    param(
        [Parameter(Mandatory = $true)] [string]$AddonXmlPath,
        [Parameter(Mandatory = $true)] [string]$Version
    )

    [xml]$xmlDoc = Get-Content -Path $AddonXmlPath
    # Use the same GitHub Pages origin as the install source. Some Fire OS/Kodi
    # builds can browse Pages but fail silently when fetching raw.githubusercontent.com.
    $baseRaw = "https://mangiafestoelectronicsllc.github.io/MEOS"

    $extensionNode = $xmlDoc.SelectSingleNode('/addon/extension[@point="xbmc.addon.repository"]')
    if (-not $extensionNode) {
        throw "Missing xbmc.addon.repository extension in $AddonXmlPath"
    }

    # Kodi filters <dir> blocks by the xbmc.addon version (ADDON_API): Leia is 18.x,
    # Matrix 19.x, Nexus 20.x, Omega 21.x. Leia honours only @minversion, so the Leia
    # block must stay reachable via minversion 0.0.0 while @maxversion hides it from 19+.
    $dirDefinitions = @(
        @{ MinVersion = "19.0.0"; MaxVersion = $null; Info = "addons.xml"; Checksum = "addons.xml.md5"; DataDir = "zips/" },
        @{ MinVersion = "0.0.0"; MaxVersion = "18.9.9"; Info = "addons-k18.xml"; Checksum = "addons-k18.xml.md5"; DataDir = "zips-k18/" }
    )

    $extensionNode.SelectNodes("dir") | ForEach-Object { $extensionNode.RemoveChild($_) | Out-Null }

    foreach ($definition in $dirDefinitions) {
        $dirNode = $xmlDoc.CreateElement("dir")
        $dirNode.SetAttribute("minversion", $definition.MinVersion)
        if ($definition.MaxVersion) {
            $dirNode.SetAttribute("maxversion", $definition.MaxVersion)
        }

        $infoNode = $xmlDoc.CreateElement("info")
        $infoNode.SetAttribute("compressed", "false")
        $infoNode.InnerText = "{0}/{1}" -f $baseRaw, $definition.Info
        $dirNode.AppendChild($infoNode) | Out-Null

        $checksumNode = $xmlDoc.CreateElement("checksum")
        $checksumNode.InnerText = "{0}/{1}" -f $baseRaw, $definition.Checksum
        $dirNode.AppendChild($checksumNode) | Out-Null

        $datadirNode = $xmlDoc.CreateElement("datadir")
        $datadirNode.SetAttribute("zip", "true")
        $datadirNode.InnerText = "{0}/{1}" -f $baseRaw, $definition.DataDir
        $dirNode.AppendChild($datadirNode) | Out-Null

        $extensionNode.AppendChild($dirNode) | Out-Null
    }

    $xmlDoc.Save($AddonXmlPath)
}

Set-RepositoryFeedUrls -AddonXmlPath $RepositoryAddonXmlPath -Version $repositoryVersion
[xml]$repositoryXml = Get-Content -Path $RepositoryAddonXmlPath

if (-not (Test-Path $ZipsRoot)) {
    New-Item -ItemType Directory -Path $ZipsRoot | Out-Null
}

$pluginZipDir = Join-Path $ZipsRoot $pluginId
if (-not (Test-Path $pluginZipDir)) {
    New-Item -ItemType Directory -Path $pluginZipDir | Out-Null
}

# Keep feed clean for Kodi clients: remove previous plugin-version artifacts.
Get-ChildItem -Path $pluginZipDir -Filter ("{0}-*.zip" -f $pluginId) -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue

$legacyPluginZipPath = Join-Path $ZipsRoot ("{0}.zip" -f $pluginId)
if (Test-Path $legacyPluginZipPath) {
    Remove-Item -Path $legacyPluginZipPath -Force
}

$hubZipDir = Join-Path $ZipsRoot $hubId
if (-not (Test-Path $hubZipDir)) {
    New-Item -ItemType Directory -Path $hubZipDir | Out-Null
}
Get-ChildItem -Path $hubZipDir -Filter ("{0}-*.zip" -f $hubId) -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue

# Leia resolves downloads as <datadir>/<id>/<id>-<version>.zip, so the Kodi 18 builds
# need their own datadir rather than a "-k18" filename suffix inside zips/.
$pluginZipK18Dir = Join-Path $ZipsK18Root $pluginId
$hubZipK18Dir = Join-Path $ZipsK18Root $hubId
foreach ($k18Dir in @($pluginZipK18Dir, $hubZipK18Dir)) {
    if (-not (Test-Path $k18Dir)) {
        New-Item -ItemType Directory -Path $k18Dir -Force | Out-Null
    }
    Get-ChildItem -Path $k18Dir -Filter "*.zip" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
}

$k18PluginZipPath = Join-Path $pluginZipK18Dir ("{0}-{1}.zip" -f $pluginId, $pluginVersion)
$k21PluginZipPath = Join-Path $pluginZipDir ("{0}-{1}.zip" -f $pluginId, $pluginVersion)
$k18HubZipPath = Join-Path $hubZipK18Dir ("{0}-{1}.zip" -f $hubId, $hubVersion)
$hubZipPath = Join-Path $hubZipDir ("{0}-{1}.zip" -f $hubId, $hubVersion)

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

foreach ($buildProfile in $profileDefinitions) {
    $pluginStagingRoot = Join-Path $env:TEMP ("meos-plugin-{0}-stage-{1}" -f $buildProfile.Name, [guid]::NewGuid().ToString("N"))
    $pluginStagingDir = Join-Path $pluginStagingRoot $pluginId
    New-Item -ItemType Directory -Path $pluginStagingDir -Force | Out-Null

    Copy-Item -Path (Join-Path $PluginSourceDir "*") -Destination $pluginStagingDir -Recurse -Force

    Get-ChildItem -Path $pluginStagingDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $pluginStagingDir -Recurse -File -Include "*.pyc", "*.pyo" -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

    $stagedAddonXmlPath = Join-Path $pluginStagingDir "addon.xml"
    Set-PluginPythonDependencyVersion -AddonXmlPath $stagedAddonXmlPath -PythonDependencyVersion $buildProfile.PythonDependencyVersion

    New-ZipFromFolder -SourceFolder $pluginStagingRoot -DestinationZip $buildProfile.ProfileZipPath
    Copy-Item -Path $buildProfile.ProfileZipPath -Destination $buildProfile.InstallZipPath -Force

    Remove-Item -Path $pluginStagingRoot -Recurse -Force
}

# Hub uses the same K18 (Python 2)/K21 (Python 3) split as the plugin, so
# MEOS Hub - the all-in-one add-on - installs directly on Kodi 18.7 too,
# not just Kodi 19+/Firestick.
$hubProfileDefinitions = @(
    @{
        Name                    = "k18"
        PythonDependencyVersion = "2.25.0"
        ProfileZipPath          = $k18HubZipPath
        InstallZipPath          = $HubSingleInstallZipPath
    },
    @{
        Name                    = "k21"
        PythonDependencyVersion = "3.0.0"
        ProfileZipPath          = $hubZipPath
        InstallZipPath          = $null
    }
)

foreach ($hubBuildProfile in $hubProfileDefinitions) {
    $hubStagingRoot = Join-Path $env:TEMP ("meoshub-{0}-stage-{1}" -f $hubBuildProfile.Name, [guid]::NewGuid().ToString("N"))
    $hubStagingDir = Join-Path $hubStagingRoot $hubId
    New-Item -ItemType Directory -Path $hubStagingDir -Force | Out-Null

    Copy-Item -Path (Join-Path $HubSourceDir "*") -Destination $hubStagingDir -Recurse -Force
    Get-ChildItem -Path $hubStagingDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $hubStagingDir -Recurse -File -Include "*.pyc", "*.pyo" -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

    $stagedHubAddonXmlPath = Join-Path $hubStagingDir "addon.xml"
    Set-PluginPythonDependencyVersion -AddonXmlPath $stagedHubAddonXmlPath -PythonDependencyVersion $hubBuildProfile.PythonDependencyVersion

    New-ZipFromFolder -SourceFolder $hubStagingRoot -DestinationZip $hubBuildProfile.ProfileZipPath
    if ($hubBuildProfile.InstallZipPath) {
        Copy-Item -Path $hubBuildProfile.ProfileZipPath -Destination $hubBuildProfile.InstallZipPath -Force
    }

    Remove-Item -Path $hubStagingRoot -Recurse -Force
}

# The direct Kodi 20+ installer is intentionally a bundle: selecting one zip
# installs both the classic MEOS catalog and MEOS Hub. Repository feeds still
# publish each add-on separately so Kodi can update them independently.
$modernBundleRoot = Join-Path $env:TEMP ("meos-modern-bundle-{0}" -f [guid]::NewGuid().ToString("N"))
$modernPluginDir = Join-Path $modernBundleRoot $pluginId
$modernHubDir = Join-Path $modernBundleRoot $hubId
New-Item -ItemType Directory -Path $modernPluginDir -Force | Out-Null
New-Item -ItemType Directory -Path $modernHubDir -Force | Out-Null
Copy-Item -Path (Join-Path $PluginSourceDir "*") -Destination $modernPluginDir -Recurse -Force
Copy-Item -Path (Join-Path $HubSourceDir "*") -Destination $modernHubDir -Recurse -Force
Set-PluginPythonDependencyVersion -AddonXmlPath (Join-Path $modernPluginDir "addon.xml") -PythonDependencyVersion "3.0.0"
Set-PluginPythonDependencyVersion -AddonXmlPath (Join-Path $modernHubDir "addon.xml") -PythonDependencyVersion "3.0.0"
New-ZipFromFolder -SourceFolder $modernBundleRoot -DestinationZip $SingleInstallZipModernPath
Remove-Item -Path $modernBundleRoot -Recurse -Force

function Write-AddonsFeed {
    param(
        [Parameter(Mandatory = $true)] [string]$XmlPath,
        [Parameter(Mandatory = $true)] [string]$Md5Path,
        [Parameter(Mandatory = $true)] [string[]]$AddonXmlFragments
    )

    $content = @(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<addons>'
        $AddonXmlFragments
        '</addons>'
    ) -join "`n"

    # LF only: git normalizes CRLF on commit, which would invalidate the published md5.
    [System.IO.File]::WriteAllText($XmlPath, $content, (New-Object System.Text.UTF8Encoding($false)))

    $hash = (Get-FileHash -Path $XmlPath -Algorithm MD5).Hash.ToLowerInvariant()
    [System.IO.File]::WriteAllText($Md5Path, $hash, (New-Object System.Text.ASCIIEncoding))
}

function Get-AddonXmlWithPythonVersion {
    param(
        [Parameter(Mandatory = $true)] [System.Xml.XmlElement]$AddonElement,
        [Parameter(Mandatory = $true)] [string]$PythonDependencyVersion
    )

    $clone = $AddonElement.CloneNode($true)
    $importNode = $clone.SelectSingleNode('requires/import[@addon="xbmc.python"]')
    if (-not $importNode) {
        throw "Missing xbmc.python import in addon $($clone.id)"
    }

    $importNode.SetAttribute("version", $PythonDependencyVersion)
    return $clone.OuterXml
}

# The repository add-on lists itself so existing installs can pick up feed/URL changes;
# without this entry a client is stuck on whatever addon.xml it was first installed with.
Write-AddonsFeed -XmlPath $AddonsXmlPath -Md5Path $AddonsMd5Path -AddonXmlFragments @(
    $repositoryXml.addon.OuterXml
    $pluginXml.addon.OuterXml
    $hubXml.addon.OuterXml
)

Write-AddonsFeed -XmlPath $AddonsK18XmlPath -Md5Path $AddonsK18Md5Path -AddonXmlFragments @(
    $repositoryXml.addon.OuterXml
    (Get-AddonXmlWithPythonVersion -AddonElement $pluginXml.addon -PythonDependencyVersion "2.25.0")
    (Get-AddonXmlWithPythonVersion -AddonElement $hubXml.addon -PythonDependencyVersion "2.25.0")
)

$VersionedAddonsXmlPath = Join-Path $Root ("addons-{0}.xml" -f $repositoryVersion)
$VersionedAddonsMd5Path = Join-Path $Root ("addons-{0}.xml.md5" -f $repositoryVersion)
Copy-Item -Path $AddonsXmlPath -Destination $VersionedAddonsXmlPath -Force
Copy-Item -Path $AddonsMd5Path -Destination $VersionedAddonsMd5Path -Force

$repositoryZipPath = Join-Path $Root ("{0}-{1}.zip" -f $repositoryId, $repositoryVersion)
$repositoryStagingRoot = Join-Path $env:TEMP ("meos-repo-stage-{0}" -f [guid]::NewGuid().ToString("N"))
$repositoryStagingDir = Join-Path $repositoryStagingRoot $repositoryId
New-Item -ItemType Directory -Path $repositoryStagingDir -Force | Out-Null

Copy-Item -Path $RepositoryAddonXmlPath -Destination (Join-Path $repositoryStagingDir "addon.xml") -Force
Copy-Item -Path $AddonsXmlPath -Destination (Join-Path $repositoryStagingDir "addons.xml") -Force
Copy-Item -Path $AddonsMd5Path -Destination (Join-Path $repositoryStagingDir "addons.xml.md5") -Force

$optionalRepositoryFiles = @("icon.png", "fanart.jpg", "README.md", "LICENSE")
foreach ($fileName in $optionalRepositoryFiles) {
    $sourcePath = Join-Path $Root $fileName
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination (Join-Path $repositoryStagingDir $fileName) -Force
    }
}

New-ZipFromFolder -SourceFolder $repositoryStagingRoot -DestinationZip $repositoryZipPath
Remove-Item -Path $repositoryStagingRoot -Recurse -Force

# Serve the repository from both feeds so Kodi can upgrade it in place.
foreach ($repoFeedDir in @((Join-Path $ZipsRoot $repositoryId), (Join-Path $ZipsK18Root $repositoryId))) {
    if (-not (Test-Path $repoFeedDir)) {
        New-Item -ItemType Directory -Path $repoFeedDir -Force | Out-Null
    }
    Get-ChildItem -Path $repoFeedDir -Filter "*.zip" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
    Copy-Item -Path $repositoryZipPath -Destination (Join-Path $repoFeedDir ("{0}-{1}.zip" -f $repositoryId, $repositoryVersion)) -Force
}

Copy-Item -Path $repositoryZipPath -Destination $RepositoryZipConveniencePath -Force

if (-not (Test-Path $KodiInstallDir)) {
    New-Item -ItemType Directory -Path $KodiInstallDir | Out-Null
}

# Keep installer options minimal in KodiInstall.
Get-ChildItem -Path $KodiInstallDir -Filter "MEOS_ADDON.zip" -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $KodiInstallDir -Filter "MEOS_ADDON_K21.zip" -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $KodiInstallDir -Filter "MEOS_ADDON-*.zip" -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $KodiInstallDir -Filter "MEOS_ADDON_K21-*.zip" -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $KodiInstallDir -Filter "MEOS_ADDON_K18-*.zip" -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $KodiInstallDir -Filter "MEOS_ADDON_K20PLUS-*.zip" -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $KodiInstallDir -Filter "MEOS_HUB_K18-*.zip" -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $KodiInstallDir -Filter "repository.meos-*.zip" -File -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue

Copy-Item -Path $SingleInstallZipPath -Destination (Join-Path $KodiInstallDir "MEOS_ADDON_K18.zip") -Force
Copy-Item -Path $SingleInstallZipModernPath -Destination (Join-Path $KodiInstallDir "MEOS_ADDON_K20PLUS.zip") -Force
Copy-Item -Path $HubSingleInstallZipPath -Destination (Join-Path $KodiInstallDir "MEOS_HUB_K18.zip") -Force
Copy-Item -Path $RepositoryZipConveniencePath -Destination (Join-Path $KodiInstallDir "repository.meos.zip") -Force

function Write-DocsIndex {
    param(
        [Parameter(Mandatory = $true)] [string]$Root,
        [Parameter(Mandatory = $true)] [string]$RepositoryVersion
    )

    $docsDir = Join-Path $Root "docs"
    if (-not (Test-Path $docsDir)) {
        New-Item -ItemType Directory -Path $docsDir | Out-Null
    }

    Copy-Item -Path $RepositoryZipConveniencePath -Destination (Join-Path $docsDir "repository.meos.zip") -Force
    Copy-Item -Path $SingleInstallZipPath -Destination (Join-Path $docsDir "MEOS_ADDON_K18.zip") -Force
    Copy-Item -Path $SingleInstallZipModernPath -Destination (Join-Path $docsDir "MEOS_ADDON_K20PLUS.zip") -Force
    Copy-Item -Path $HubSingleInstallZipPath -Destination (Join-Path $docsDir "MEOS_HUB_K18.zip") -Force

    $links = @(
        @{ Name = "repository.meos.zip (install this first - auto-updates both add-ons on Kodi 18.7 and Kodi 19+/20+)"; Href = "repository.meos.zip" },
        @{ Name = "MEOS_ADDON_K18.zip (Kodi 18.7 direct install, classic add-on)"; Href = "MEOS_ADDON_K18.zip" },
        @{ Name = "MEOS_ADDON_K20PLUS.zip (Kodi 19+/Firestick direct install, MEOS + MEOS Hub bundle)"; Href = "MEOS_ADDON_K20PLUS.zip" },
        @{ Name = "MEOS_HUB_K18.zip (Kodi 18.7 direct install, MEOS Hub all-in-one)"; Href = "MEOS_HUB_K18.zip" }
    )

    # Keep this as a plain link list. Kodi's HTTP directory parser on Android is
    # stricter than a desktop browser and may ignore links nested in list markup.
    $listItems = ($links | ForEach-Object { '<a href="' + $_.Href + '">' + $_.Name + '</a><br />' }) -join [Environment]::NewLine

    $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>MEOS Kodi Repository - v$RepositoryVersion</title>
</head>
<body>
<h1>MEOS Kodi Repository (v$RepositoryVersion)</h1>
<p>Add this URL as a Kodi File Manager source, then use Install from zip file.</p>
$listItems
</body>
</html>
"@

    [System.IO.File]::WriteAllText((Join-Path $docsDir "index.html"), $html, (New-Object System.Text.UTF8Encoding($false)))
}

Write-DocsIndex -Root $Root -RepositoryVersion $repositoryVersion

Write-Host "Build completed"
if (-not $NoAutoBump) {
    Write-Host "Plugin version: $($pluginBump.OldVersion) -> $($pluginBump.NewVersion)"
    Write-Host "Hub version: $($hubBump.OldVersion) -> $($hubBump.NewVersion)"
    Write-Host "Repository version: $($repositoryBump.OldVersion) -> $($repositoryBump.NewVersion)"
}
else {
    Write-Host "Auto version bump skipped (-NoAutoBump)"
}
Write-Host "Plugin zip (Kodi 18): $k18PluginZipPath"
Write-Host "Plugin zip (Kodi 21/22): $k21PluginZipPath"
Write-Host "Hub zip (Kodi 18): $k18HubZipPath"
Write-Host "Hub zip (Kodi 19+): $hubZipPath"
Write-Host "Single install zip (Kodi 18): $SingleInstallZipPath"
Write-Host "Single install zip (Kodi 20+): $SingleInstallZipModernPath"
Write-Host "Hub single install zip (Kodi 18): $HubSingleInstallZipPath"
Write-Host "Repository zip: $repositoryZipPath"
Write-Host "Repository zip (convenience): $RepositoryZipConveniencePath"
Write-Host "KodiInstall folder: $KodiInstallDir"
Write-Host "Updated: $AddonsXmlPath"
Write-Host "Updated: $AddonsMd5Path"
Write-Host "Updated: $AddonsK18XmlPath"
Write-Host "Updated: $AddonsK18Md5Path"
Write-Host "Repository zip includes: addon.xml, addons.xml, and addons.xml.md5"

& (Join-Path $PSScriptRoot "verify-repo-feed.ps1") -Root $Root
if ($LASTEXITCODE -ne 0) {
    throw "Repository feed verification failed - do not publish this build"
}
