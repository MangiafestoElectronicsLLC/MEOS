Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$xml = Join-Path $root "addons.xml"
$md5 = Join-Path $root "addons.xml.md5"

$text = [System.IO.File]::ReadAllText($xml)
if ([string]::IsNullOrWhiteSpace($text)) {
    throw "addons.xml is empty - refusing to write a checksum"
}

$normalized = $text.Replace("`r`n", "`n")
[System.IO.File]::WriteAllText($xml, $normalized, (New-Object System.Text.UTF8Encoding($false)))

$hash = (Get-FileHash -Path $xml -Algorithm MD5).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText($md5, $hash, (New-Object System.Text.ASCIIEncoding))

Write-Host ("addons.xml bytes : {0}" -f (Get-Item $xml).Length)
Write-Host ("addons.xml md5   : {0}" -f $hash)
