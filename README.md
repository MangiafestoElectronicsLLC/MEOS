# MEOS

MEOS is a Kodi repository plus a companion video add-on with a clean install path for Firestick and other Kodi devices.

## Install (any Kodi device, not just this PC)

1. Recommended: browse straight from Kodi using the GitHub Pages install source
- In Kodi: Settings -> File manager -> Add source -> enter `https://mangiafestoelectronicsllc.github.io/MEOS/`.
- Add-ons -> Install from zip file -> pick that source -> choose `repository.meos.zip` (installs the repo, which then auto-updates itself and MEOS from `addons.xml`).
- One-time GitHub setup: open repo Settings -> Pages, set Source to `GitHub Actions`, then run the `Deploy Kodi install page` workflow once from the Actions tab. Wait for it to finish before adding the Kodi source. The workflow publishes `/docs`, including the ZIP files.
- If the URL returns 404 or Kodi says "Couldn't retrieve directory information", Pages has not deployed yet. Do not add the GitHub repository URL as a Kodi source; wait for the Pages workflow or use the direct ZIP fallback below.

2. Why plain raw GitHub URLs don't work as a Kodi source
- `raw.githubusercontent.com` serves individual files but has no browsable directory listing, so Kodi File Manager shows "Couldn't retrieve directory information" if you add it directly as a source.
- The GitHub Pages source contains the ZIP files and an index with relative links, so Kodi does not need to browse raw GitHub.
- Do not use the GitHub repository page or `https://github.com/MangiafestoElectronicsLLC/MEOS.git` as a Kodi source.

3. Manual transfer fallback (no network browsing on the device)
- Download `repository.meos.zip` from `https://github.com/MangiafestoElectronicsLLC/MEOS/raw/refs/heads/main/repository.meos.zip` (or the matching direct ZIP) on any PC/phone.
- Copy it to the device via USB/cloud storage, then Install from zip file locally.

4. Kodi version guidance
- Kodi 19+ / Firestick: `MEOS_ADDON_K20PLUS.zip` or the repository install above.
- Kodi 18.x: `MEOS_ADDON_K18.zip`.

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
