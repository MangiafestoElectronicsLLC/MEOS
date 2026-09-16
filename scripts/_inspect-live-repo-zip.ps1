$ProgressPreference = "SilentlyContinue"
if (-not ('System.IO.Compression.ZipFile' -as [type])) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
}

$url = "https://mangiafestoelectronicsllc.github.io/MEOS/repository.meos.zip"
$zip = Join-Path ([System.IO.Path]::GetTempPath()) "meos_live_repo.zip"
Invoke-WebRequest $url -OutFile $zip -UseBasicParsing -Headers @{ "Cache-Control" = "no-cache" }

Write-Host ("downloaded {0} bytes from {1}" -f (Get-Item $zip).Length, $url)

$archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
try {
    Write-Host ""
    Write-Host "entries:"
    $archive.Entries | ForEach-Object { Write-Host ("  {0}" -f $_.FullName) }

    $entry = $archive.GetEntry("repository.meos/addon.xml")
    $reader = New-Object System.IO.StreamReader($entry.Open())
    try { $addonXml = $reader.ReadToEnd() } finally { $reader.Dispose() }
}
finally {
    $archive.Dispose()
}

Write-Host ""
Write-Host "packaged addon.xml:"
Write-Host $addonXml
