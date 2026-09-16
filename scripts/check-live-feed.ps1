[CmdletBinding()]
param(
    [string[]]$BaseUrls = @(
        "https://mangiafestoelectronicsllc.github.io/MEOS",
        "https://raw.githubusercontent.com/MangiafestoElectronicsLLC/MEOS/main"
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$feeds = @(
    @{ Name = "Kodi 19+"; Xml = "addons.xml"; Md5 = "addons.xml.md5"; DataDir = "zips" },
    @{ Name = "Kodi 18"; Xml = "addons-k18.xml"; Md5 = "addons-k18.xml.md5"; DataDir = "zips-k18" }
)

$headers = @{ "Cache-Control" = "no-cache"; "Pragma" = "no-cache" }
$failures = 0

foreach ($base in $BaseUrls) {
    Write-Host ""
    Write-Host ("=== {0} ===" -f $base)

    foreach ($feed in $feeds) {
        $xmlPath = Join-Path ([System.IO.Path]::GetTempPath()) ("meos_live_{0}" -f $feed.Xml)
        $md5Path = "$xmlPath.md5"

        try {
            Invoke-WebRequest "$base/$($feed.Xml)" -OutFile $xmlPath -UseBasicParsing -Headers $headers -TimeoutSec 30
            Invoke-WebRequest "$base/$($feed.Md5)" -OutFile $md5Path -UseBasicParsing -Headers $headers -TimeoutSec 30
        }
        catch {
            Write-Host ("  FAIL  {0} feed unreachable: {1}" -f $feed.Name, $_.Exception.Message)
            $failures++
            continue
        }

        $computed = (Get-FileHash -Path $xmlPath -Algorithm MD5).Hash.ToLowerInvariant()
        $published = ([System.IO.File]::ReadAllText($md5Path)).Trim().ToLowerInvariant()

        if ($computed -ne $published) {
            Write-Host ("  FAIL  {0} feed checksum mismatch: published {1}, computed {2}" -f $feed.Name, $published, $computed)
            $failures++
            continue
        }

        Write-Host ("  ok    {0} feed: {1} bytes, md5 {2}" -f $feed.Name, (Get-Item $xmlPath).Length, $computed)

        # Every advertised add-on must actually be downloadable from its datadir.
        [xml]$doc = Get-Content -Path $xmlPath -Raw
        foreach ($addon in $doc.addons.addon) {
            $addonId = $addon.GetAttribute("id")
            $addonVersion = $addon.GetAttribute("version")
            $zipUrl = "{0}/{1}/{2}/{2}-{3}.zip" -f $base, $feed.DataDir, $addonId, $addonVersion

            try {
                $response = Invoke-WebRequest -Uri $zipUrl -Method Head -UseBasicParsing -TimeoutSec 30
                Write-Host ("  ok    {0} {1} -> HTTP {2}" -f $addonId, $addonVersion, $response.StatusCode)
            }
            catch {
                Write-Host ("  FAIL  {0} {1} not downloadable at {2}" -f $addonId, $addonVersion, $zipUrl)
                $failures++
            }
        }
    }
}

Write-Host ""
if ($failures -gt 0) {
    Write-Host ("LIVE FEED CHECK FAILED ({0} problem(s))" -f $failures)
    exit 1
}

Write-Host "LIVE FEED CHECK PASSED"
exit 0
