# MEOS

MEOS is a Kodi repository plus two companion video add-ons with a clean install path for Firestick, Kodi 18.7 (Leia) and Kodi 19+/20+ (Matrix/Nexus/Omega) devices:

- `plugin.video.meos` - the classic sample/provider add-on (legal sample streams + provider scaffolding, Installed Add-ons Hub).
- `plugin.video.meoshub` - **MEOS Hub**, the all-in-one add-on that unifies free/legal content, metadata scrapers and *any* of your other installed Kodi add-ons in one interface.

Both add-ons ship in two build profiles: a Python 3 build for Kodi 19+/20+ and Firestick, and a separate Python 2 build for Kodi 18.7. Pick the guidance below for your situation.

## Install (any Kodi device, local or global)

### A. Global / on-device browsing (no PC needed) - Kodi 19+/20+ only
Use this when the device itself can browse the internet from Kodi's File Manager. Repository auto-updates work only on Kodi 19+ (the repository's `addons.xml` targets Python 3), so this path is for Matrix/Nexus/Omega and modern Firestick builds.

1. In Kodi: **Settings -> File manager -> Add source** -> enter `https://mangiafestoelectronicsllc.github.io/MEOS/`.
2. **Add-ons -> Install from zip file** -> pick that source -> choose `repository.meos.zip`.
3. This installs the MEOS repository, which auto-updates itself plus both `plugin.video.meos` and `MEOS Hub` from `addons.xml`.
4. In Kodi, go to **Add-ons -> Install from repository -> MEOS Repository** and install **MEOS Hub** (and/or the classic MEOS add-on) from there.
5. One-time GitHub setup (repo maintainers only): open repo **Settings -> Pages**, set Source to `GitHub Actions`, then run the `Deploy Kodi install page` workflow once from the Actions tab. Wait for it to finish before adding the Kodi source. The workflow publishes `/docs`, including all ZIP files.
6. If the URL returns 404 or Kodi says "Couldn't retrieve directory information", Pages has not deployed yet. Do not add the GitHub repository URL as a Kodi source; wait for the Pages workflow or use the direct ZIP fallback below.

### B. Local transfer (any Kodi version, any device, no network browsing needed)
Use this for Kodi 18.7, devices that can't browse the GitHub Pages source, or offline installs.

1. Download the ZIP(s) you need on any PC/phone from either:
   - `https://mangiafestoelectronicsllc.github.io/MEOS/` (if Pages is deployed), or
   - `https://github.com/MangiafestoElectronicsLLC/MEOS/raw/refs/heads/main/<file>.zip` for a specific file.
2. Copy the ZIP(s) to the device via USB/cloud storage/local network share.
3. In Kodi: **Add-ons -> Install from zip file** -> browse to the copied file(s) and install directly. No repository install is required for this path, and it works on every supported Kodi version.

### Why plain raw GitHub URLs don't work as a Kodi source
- `raw.githubusercontent.com` serves individual files but has no browsable directory listing, so Kodi File Manager shows "Couldn't retrieve directory information" if you add it directly as a source.
- The GitHub Pages source contains the ZIP files and an index with relative links, so Kodi does not need to browse raw GitHub.
- Do not use the GitHub repository page or `https://github.com/MangiafestoElectronicsLLC/MEOS.git` as a Kodi source.

## Which ZIP for which Kodi version

| File | Add-on | Kodi version | Install method |
| --- | --- | --- | --- |
| `repository.meos.zip` | MEOS Repository (both add-ons) | 19+/20+/Firestick | Add source + Install from zip, then Install from repository (auto-updates) |
| `MEOS_ADDON_K20PLUS.zip` | `plugin.video.meos` | 19+/20+/Firestick | Direct Install from zip file |
| `MEOS_ADDON_K18.zip` | `plugin.video.meos` | 18.7 (Leia) | Direct Install from zip file |
| `MEOS_HUB_K18.zip` | MEOS Hub (`plugin.video.meoshub`) | 18.7 (Leia) | Direct Install from zip file |

Notes:
- On Kodi 18.7, always use the `_K18` zips and install directly - the repository's `addons.xml` targets Kodi 19+ only, so repository auto-update is not available on Leia. Reinstall the matching `_K18` zip manually when a new MEOS version is released.
- On Kodi 19+/20+/Firestick, either the repository (recommended, auto-updates) or the direct `_K20PLUS`/repository-installed Hub zip works.
- MEOS Hub on Kodi 19+ is installed via the repository (step A.4 above) or by downloading `plugin.video.meoshub-<version>.zip` from `zips/plugin.video.meoshub/` and installing it directly.

## What’s Included

- `repository.meos`: Kodi repository package (feeds both `plugin.video.meos` and `plugin.video.meoshub`)
- `plugin.video.meos`: legal sample streams and provider scaffolding
- `plugin.video.meoshub` (MEOS Hub): all-in-one hub - free/legal content, metadata scrapers, and routing into any installed Kodi add-on (see `plugin.video.meoshub/README.md` for details)
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
