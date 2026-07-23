# MEOS

MEOS is a Kodi repository plus a companion video add-on with a clean install path for Firestick and other Kodi devices.

## Install

Use the direct ZIP links instead of the GitHub page URL.

1. Repository install for Kodi
- Download `repository.meos.zip` directly from GitHub Releases or the raw file URL.
- Copy it to the Firestick or another device Kodi can browse.
- In Kodi: Add-ons -> Install from zip file -> choose `repository.meos.zip`.
- Then open Install from repository -> MEOS Repository -> install MEOS.

2. Firestick / Kodi 21 direct install
- Download `MEOS_ADDON_K21.zip` from the repository.
- Copy it to the device.
- In Kodi, choose Install from zip file and select `MEOS_ADDON_K21.zip`.

3. Older Kodi builds
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
- If raw browsing is blocked on the device, download the ZIP on a PC and transfer it manually.
- The repository feed points to the raw GitHub XML and ZIP files under `zips/`.

## Community Validation API

MEOS can now share stream validation status across different devices/users when they point to the same API.

### Super Simple Setup (Non-Technical)

1. In Kodi MEOS home, open `Community Validation Quick Setup`.
2. Paste your API URL.
3. Paste your API key.
4. Optional: paste signature secret only if your server requires signatures.

That is enough to enable cross-device validation.

Configure in MEOS Settings:
- Community validation: enable shared remote status
- Community validation API base URL
- Community validation API key
- Community validation signature secret

Expected endpoint contract (base URL + path):

1. GET `/validation?key=<stream-key>`
- Response JSON can be any of:
	- `{ "vote": "up" }`
	- `{ "vote": "down" }`
	- `{ "status": "up" }`
	- `{ "validated": true }`
	- `{ "data": { "vote": "up" } }`

2. POST `/validation`
- Request JSON:
	- `key`: canonical stream key (provider item key or integrated plugin shared key)
	- `vote`: `up` or `down`
	- `source`: `provider` or `integrated`
	- `addon`, `version`, `timestamp`
- Response: any valid JSON object (MEOS treats HTTP+JSON success as accepted).

Header behavior:
- If API key is set, MEOS sends both `X-API-Key` and `Authorization: Bearer <key>`.
- If signature secret is set, MEOS also sends:
	- `X-MEOS-Timestamp`
	- `X-MEOS-Signature`
	- `X-MEOS-Signature-Version: v1`

Secure baseline (recommended and now default in reference worker):
- Set `API_KEY` on server and in add-on settings.
- Set `SIGNING_SECRET` on server and `remote_validation_signature_secret` in add-on settings.
- Keep `REQUIRE_SIGNATURE=true`.
- Keep `RATE_LIMIT_ENABLED=true` with conservative limits (default `60` requests per `60` seconds per IP).

If you are using simple mode for non-technical users:
- Keep API key required.
- Signatures can be left blank in the add-on only when server-side `REQUIRE_SIGNATURE=false`.

Server hardening recommendation:
- Optional signature validation and IP rate limiting reference implementation is included at:
	- `scripts/community-validation-worker.js`
	- `scripts/community-validation-worker.md`
