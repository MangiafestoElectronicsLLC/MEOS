Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$verify = Join-Path $PSScriptRoot "verify-repo-feed.ps1"
$sandbox = Join-Path ([System.IO.Path]::GetTempPath()) ("meos-verify-negative-" + [guid]::NewGuid().ToString("N"))

function Invoke-Verify {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $verify -Root $sandbox *> $null
    return $LASTEXITCODE
}

function New-Sandbox {
    if (Test-Path $sandbox) { Remove-Item $sandbox -Recurse -Force }
    New-Item -ItemType Directory -Path $sandbox -Force | Out-Null
    foreach ($name in @("addon.xml", "addons.xml", "addons.xml.md5", "addons-k18.xml", "addons-k18.xml.md5")) {
        Copy-Item (Join-Path $root $name) (Join-Path $sandbox $name) -Force
    }
    Copy-Item (Join-Path $root "zips") (Join-Path $sandbox "zips") -Recurse -Force
    Copy-Item (Join-Path $root "zips-k18") (Join-Path $sandbox "zips-k18") -Recurse -Force
}

$results = @()

New-Sandbox
$results += @{ Name = "clean tree passes"; Expected = 0; Actual = (Invoke-Verify) }

New-Sandbox
$p = Join-Path $sandbox "addons.xml"
[System.IO.File]::WriteAllText($p, ([System.IO.File]::ReadAllText($p)).Replace("`n", "`r`n"))
$results += @{ Name = "CRLF in addons.xml is rejected"; Expected = 1; Actual = (Invoke-Verify) }

New-Sandbox
[System.IO.File]::WriteAllText((Join-Path $sandbox "addons.xml.md5"), "00000000000000000000000000000000")
$results += @{ Name = "stale md5 is rejected"; Expected = 1; Actual = (Invoke-Verify) }

New-Sandbox
Remove-Item (Join-Path $sandbox "zips-k18\plugin.video.meoshub") -Recurse -Force
$results += @{ Name = "missing Kodi 18 zip is rejected"; Expected = 1; Actual = (Invoke-Verify) }

New-Sandbox
$k18 = Join-Path $sandbox "addons-k18.xml"
[System.IO.File]::WriteAllText($k18, ([System.IO.File]::ReadAllText($k18)).Replace('version="2.25.0"', 'version="3.0.0"'))
$hash = (Get-FileHash -Path $k18 -Algorithm MD5).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText((Join-Path $sandbox "addons-k18.xml.md5"), $hash)
$results += @{ Name = "Python 3 in the Kodi 18 feed is rejected"; Expected = 1; Actual = (Invoke-Verify) }

New-Sandbox
$addonXml = Join-Path $sandbox "addon.xml"
[System.IO.File]::WriteAllText($addonXml, ([System.IO.File]::ReadAllText($addonXml)).Replace(' minversion="19.0.0"', ''))
$results += @{ Name = "missing minversion guard is rejected"; Expected = 1; Actual = (Invoke-Verify) }

if (Test-Path $sandbox) { Remove-Item $sandbox -Recurse -Force }

$failed = 0
foreach ($r in $results) {
    if ($r.Actual -eq $r.Expected) {
        Write-Host ("  ok    {0}" -f $r.Name)
    }
    else {
        Write-Host ("  FAIL  {0} (expected exit {1}, got {2})" -f $r.Name, $r.Expected, $r.Actual)
        $failed++
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("VERIFIER SELF-TEST FAILED ({0} case(s))" -f $failed)
    exit 1
}

Write-Host "VERIFIER SELF-TEST PASSED"
exit 0
