# MEOS

MEOS is a Kodi repository plus a companion video add-on with a clean install path for Firestick and other Kodi devices.

## Install

Use the direct ZIP links instead of the GitHub page URL.

1. Recommended repository install (all devices)
- Download `repository.meos.zip` directly from GitHub Releases or the raw file URL.
- Copy it to the Firestick or another device Kodi can browse.
- In Kodi: Add-ons -> Install from zip file -> choose `repository.meos.zip`.
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

## Integrating Other Add-ons (Example: ScrubsV2)

You can merge installed add-on content into MEOS category pages (Movies, TV Shows, Cable TV, Live Channels, Sports, and more).

1. Install and enable the external addon in Kodi first (for example, ScrubsV2).
2. In MEOS, open Integrate Other Add-ons -> Select Installed Add-ons.
3. Toggle the addon you want, then go back to Integrate Other Add-ons.
4. Open Integration Inspector -> Scan This Add-on Now to build category matches.
5. Open One-Click Movies, One-Click TV Shows, Cable TV, Live Channels, or Sports Hub.
6. Use entries labeled with [Integrated AddonName] to browse/play merged external content.

Tips for hard-to-match add-ons:
- Open Installed Add-ons Hub -> browse that addon.
- On a folder or playable item, use Map to MEOS and assign it to Movies/TV/Cable/PPV/Live/Sports/Docs.
- Re-open Integration Inspector and scan again.

Quick manual scan from hold-select context menu:
- In Installed Add-ons Hub (or any integrated browse page), highlight a folder/item and hold Select/OK to open the context menu.
- Use MEOS: Scan This Add-on For Content to refresh matching and cache for that add-on.
- Use MEOS: Scan This Folder To Add to auto-map that folder into a MEOS category and refresh integration.

Search All modes:
- Search All now includes three modes:
	- Search Everything (Providers + Integrated)
	- Search Providers Only
	- Search Integrated Add-ons Only
- Integrated mode returns playable/folder results from selected integrated add-ons so external addon content appears directly in MEOS search results.

This flow is designed for broad compatibility with many addon menu structures, including deep nested category trees.

## Notes

- Do not use `https://github.com/MangiafestoElectronicsLLC/MEOS.git` or the GitHub page URL as a Kodi source.
- If remote browsing is blocked on the device, download ZIP files on a PC/phone and transfer them manually.
- The repository feed points to the raw GitHub XML and ZIP files under `zips/`.
