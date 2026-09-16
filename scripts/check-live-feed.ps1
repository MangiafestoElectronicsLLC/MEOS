$ProgressPreference = "SilentlyContinue"
$bases = @(
    "https://mangiafestoelectronicsllc.github.io/MEOS",
    "https://raw.githubusercontent.com/MangiafestoElectronicsLLC/MEOS/main"
)
$xmlPath = Join-Path $env:TEMP "meos_live_addons.xml"
$md5Path = Join-Path $env:TEMP "meos_live_addons.md5"
$headers = @{ "Cache-Control" = "no-cache"; "Pragma" = "no-cache" }

foreach ($base in $bases) {
    Write-Host ""
    Write-Host ("=== {0} ===" -f $base)
    try {
        Invoke-WebRequest "$base/addons.xml" -OutFile $xmlPath -UseBasicParsing -Headers $headers -TimeoutSec 30
        Invoke-WebRequest "$base/addons.xml.md5" -OutFile $md5Path -UseBasicParsing -Headers $headers -TimeoutSec 30
    }
    catch {
        Write-Host ("Fetch failed: {0}" -f $_.Exception.Message)
        continue
    }

    $computed = (Get-FileHash -Path $xmlPath -Algorithm MD5).Hash.ToLowerInvariant()
    $published = ([System.IO.File]::ReadAllText($md5Path)).Trim().ToLowerInvariant()

    Write-Host ("served addons.xml : {0} bytes" -f (Get-Item $xmlPath).Length)
    Write-Host ("published md5     : {0}" -f $published)
    Write-Host ("computed  md5     : {0}" -f $computed)

    if ($computed -eq $published) {
        Write-Host "RESULT: MATCH - Kodi will accept the repository feed"
    }
    else {
        Write-Host "RESULT: MISMATCH - not redeployed yet"
    }
}
