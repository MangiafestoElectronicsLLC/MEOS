[CmdletBinding()]
param(
    [string]$Root
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $Root) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

# Present by default on PowerShell Core; only Windows PowerShell needs the explicit load.
if (-not ('System.IO.Compression.ZipFile' -as [type])) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
}

$script:Failures = New-Object System.Collections.Generic.List[string]

function Add-Failure {
    param([Parameter(Mandatory = $true)] [string]$Message)
    $script:Failures.Add($Message)
    Write-Host ("  FAIL  {0}" -f $Message)
}

function Add-Pass {
    param([Parameter(Mandatory = $true)] [string]$Message)
    Write-Host ("  ok    {0}" -f $Message)
}

function Get-ZipEntryText {
    param(
        [Parameter(Mandatory = $true)] [string]$ZipPath,
        [Parameter(Mandatory = $true)] [string]$EntryName
    )

    $archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        $entry = $archive.GetEntry($EntryName)
        if (-not $entry) { return $null }

        $reader = New-Object System.IO.StreamReader($entry.Open())
        try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
    }
    finally {
        $archive.Dispose()
    }
}

function Test-Feed {
    param(
        [Parameter(Mandatory = $true)] [string]$FeedName,
        [Parameter(Mandatory = $true)] [string]$XmlPath,
        [Parameter(Mandatory = $true)] [string]$Md5Path,
        [Parameter(Mandatory = $true)] [string]$DataDir,
        [Parameter(Mandatory = $true)] [string]$ExpectedPythonMajor
    )

    Write-Host ""
    Write-Host ("=== {0} ===" -f $FeedName)

    foreach ($required in @($XmlPath, $Md5Path)) {
        if (-not (Test-Path $required)) {
            Add-Failure ("missing file {0}" -f $required)
            return
        }
    }

    # A CR byte here means git will normalize the file on commit and the published
    # md5 will no longer match what Kodi downloads.
    $bytes = [System.IO.File]::ReadAllBytes($XmlPath)
    if ($bytes -contains 13) {
        Add-Failure ("{0} contains CR bytes - git will normalize it and break the checksum" -f (Split-Path $XmlPath -Leaf))
    }
    else {
        Add-Pass "LF-only line endings"
    }

    $computed = (Get-FileHash -Path $XmlPath -Algorithm MD5).Hash.ToLowerInvariant()
    $published = ([System.IO.File]::ReadAllText($Md5Path)).Trim().ToLowerInvariant()
    if ($computed -ne $published) {
        Add-Failure ("checksum mismatch: {0} has {1}, expected {2}" -f (Split-Path $Md5Path -Leaf), $published, $computed)
    }
    else {
        Add-Pass ("checksum {0}" -f $computed)
    }

    [xml]$feed = Get-Content -Path $XmlPath -Raw
    foreach ($addon in $feed.addons.addon) {
        $addonId = $addon.GetAttribute("id")
        $addonVersion = $addon.GetAttribute("version")

        $import = $addon.SelectSingleNode('requires/import[@addon="xbmc.python"]')
        if (-not $import) {
            Add-Failure ("{0}: no xbmc.python import" -f $addonId)
        }
        elseif (-not $import.GetAttribute("version").StartsWith($ExpectedPythonMajor)) {
            Add-Failure ("{0}: declares xbmc.python {1}, expected {2}x" -f $addonId, $import.GetAttribute("version"), $ExpectedPythonMajor)
        }
        else {
            Add-Pass ("{0} {1} requires xbmc.python {2}" -f $addonId, $addonVersion, $import.version)
        }

        # Kodi resolves downloads as <datadir>/<id>/<id>-<version>.zip.
        $zipPath = Join-Path (Join-Path $DataDir $addonId) ("{0}-{1}.zip" -f $addonId, $addonVersion)
        if (-not (Test-Path $zipPath)) {
            Add-Failure ("{0}: missing zip at {1}" -f $addonId, $zipPath)
            continue
        }

        $packagedXml = Get-ZipEntryText -ZipPath $zipPath -EntryName ("{0}/addon.xml" -f $addonId)
        if (-not $packagedXml) {
            Add-Failure ("{0}: zip has no {0}/addon.xml entry" -f $addonId)
            continue
        }

        [xml]$packaged = $packagedXml
        if ($packaged.addon.GetAttribute("version") -ne $addonVersion) {
            Add-Failure ("{0}: zip contains version {1}, feed advertises {2}" -f $addonId, $packaged.addon.GetAttribute("version"), $addonVersion)
            continue
        }

        $packagedImport = $packaged.addon.SelectSingleNode('requires/import[@addon="xbmc.python"]')
        if (-not $packagedImport -or -not $packagedImport.GetAttribute("version").StartsWith($ExpectedPythonMajor)) {
            Add-Failure ("{0}: packaged zip declares the wrong xbmc.python version for this feed" -f $addonId)
            continue
        }

        Add-Pass ("{0} zip matches feed" -f (Split-Path $zipPath -Leaf))
    }
}

function Test-RepositoryAddonXml {
    param([Parameter(Mandatory = $true)] [string]$AddonXmlPath)

    Write-Host ""
    Write-Host "=== repository addon.xml ==="

    [xml]$doc = Get-Content -Path $AddonXmlPath -Raw
    $extension = $doc.SelectSingleNode('/addon/extension[@point="xbmc.addon.repository"]')
    if (-not $extension) {
        Add-Failure "no xbmc.addon.repository extension"
        return
    }

    if ($extension.SelectSingleNode("info")) {
        Add-Failure "extension has a top-level <info>; Kodi would always add it as an extra unfiltered dir"
    }

    $dirs = @($extension.SelectNodes("dir"))
    if ($dirs.Count -ne 2) {
        Add-Failure ("expected 2 <dir> blocks (Kodi 19+ and Kodi 18), found {0}" -f $dirs.Count)
        return
    }

    $expectations = @(
        @{ MinVersion = "19.0.0"; MaxVersion = $null; Info = "addons.xml"; DataDir = "zips/" },
        @{ MinVersion = "0.0.0"; MaxVersion = "18.9.9"; Info = "addons-k18.xml"; DataDir = "zips-k18/" }
    )

    for ($i = 0; $i -lt 2; $i++) {
        $dir = $dirs[$i]
        $expected = $expectations[$i]

        if ($dir.GetAttribute("minversion") -ne $expected.MinVersion) {
            Add-Failure ("dir[{0}] minversion is '{1}', expected '{2}'" -f $i, $dir.GetAttribute("minversion"), $expected.MinVersion)
        }

        $actualMax = $dir.GetAttribute("maxversion")
        $expectedMax = if ($expected.MaxVersion) { $expected.MaxVersion } else { "" }
        if ($actualMax -ne $expectedMax) {
            Add-Failure ("dir[{0}] maxversion is '{1}', expected '{2}'" -f $i, $actualMax, $expectedMax)
        }

        $infoText = $dir.SelectSingleNode("info").InnerText
        if (-not $infoText.EndsWith("/" + $expected.Info)) {
            Add-Failure ("dir[{0}] info points at {1}, expected it to end with /{2}" -f $i, $infoText, $expected.Info)
        }

        $dataDirText = $dir.SelectSingleNode("datadir").InnerText
        if (-not $dataDirText.EndsWith("/" + $expected.DataDir)) {
            Add-Failure ("dir[{0}] datadir points at {1}, expected it to end with /{2}" -f $i, $dataDirText, $expected.DataDir)
        }
    }

    if ($script:Failures.Count -eq 0) {
        Add-Pass "two version-scoped <dir> blocks (Kodi 19+ -> zips/, Kodi 18 -> zips-k18/)"
    }
}

Write-Host ("Verifying MEOS repository feed in {0}" -f $Root)

Test-RepositoryAddonXml -AddonXmlPath (Join-Path $Root "addon.xml")

Test-Feed -FeedName "Kodi 19+ feed (addons.xml)" `
    -XmlPath (Join-Path $Root "addons.xml") `
    -Md5Path (Join-Path $Root "addons.xml.md5") `
    -DataDir (Join-Path $Root "zips") `
    -ExpectedPythonMajor "3."

Test-Feed -FeedName "Kodi 18 feed (addons-k18.xml)" `
    -XmlPath (Join-Path $Root "addons-k18.xml") `
    -Md5Path (Join-Path $Root "addons-k18.xml.md5") `
    -DataDir (Join-Path $Root "zips-k18") `
    -ExpectedPythonMajor "2."

Write-Host ""
if ($script:Failures.Count -gt 0) {
    Write-Host ("FEED VERIFICATION FAILED ({0} problem(s))" -f $script:Failures.Count)
    exit 1
}

Write-Host "FEED VERIFICATION PASSED"
exit 0
