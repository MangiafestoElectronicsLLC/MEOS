# MEOS

MEOS is a Kodi repository plus a companion video add-on with a clean install path for Firestick and other Kodi devices.

## Install

Use the direct ZIP links instead of the GitHub page URL.

1. Recommended repository install (all devices)
- Download repository ZIP directly:
  https://raw.githubusercontent.com/MangiafestoElectronicsLLC/MEOS/main/repository.meos.zip
- In Kodi: Add-ons -> Install from zip file -> choose the downloaded `repository.meos.zip`.
- Then open Install from repository -> MEOS Repository -> install MEOS.

2. Why Kodi File Manager shows "Unable to connect"
- `raw.githubusercontent.com` serves files, but does not provide browsable directory listings.
- Kodi File Manager expects a directory index when you add a web source.
- A direct `.zip` URL is a file, not a directory source, so Kodi still warns that it cannot retrieve directory information.
- If you paste a raw GitHub URL as a source, Kodi commonly shows "Couldn't retrieve directory information".
- This does not mean your repository ZIP is broken. The ZIP URLs are valid; the source browsing method is the issue.

3. Firestick / Kodi 21 direct install
- Download `MEOS_ADDON_K21.zip` from the repository.
- Copy it to the device.
- In Kodi, choose Install from zip file and select `MEOS_ADDON_K21.zip`.

4. Older Kodi builds
- Use `MEOS_ADDON.zip` or install the repository first and let Kodi resolve the correct package.

## What’s Included

- `repository.meos`: Kodi repository package
- `plugin.video.meos`: legal sample streams and provider scaffolding
- `Installed Add-ons Hub`: browse installed add-ons from inside MEOS
- Installed add-on scanning includes both common Kodi video add-on types.
- Integration Inspector now includes a per-add-on scan action that rebuilds the full integrated menu set.
- Integrated Add-ons has a separate cached view with category headers that persists outside Manual Favorites.

## Notes

- Do not use `https://github.com/MangiafestoElectronicsLLC/MEOS.git` as a Kodi source.
- If remote browsing is blocked on the device, download ZIP files on a PC/phone and transfer them manually.
- The repository feed points to the raw GitHub XML and ZIP files under `zips/`.
- Repository feed files used by Kodi after repository install:
  - https://raw.githubusercontent.com/MangiafestoElectronicsLLC/MEOS/main/addons-1.0.17.xml
  - https://raw.githubusercontent.com/MangiafestoElectronicsLLC/MEOS/main/zips/plugin.video.meos/plugin.video.meos-1.0.17.zip
