# MEOS Hub

MEOS Hub is a single, all-in-one Kodi add-on that lets you browse, search
and play content from multiple sources - free/legal streams, metadata
scrapers, and your existing installed Kodi add-ons - **inside one unified
interface**, without switching between add-ons.

MEOS Hub never copies, bundles, or scrapes another add-on's source code. It
only uses Kodi's own JSON-RPC API to find add-ons you already have
installed and hand you a normal `plugin://` link into their menus
("routing"). Playback of MEOS Hub's own free/legal content uses the
standard `xbmcplugin.setResolvedUrl` API.

---

## 1. How it works

```
default.py            -> Kodi calls this. It just forwards argv to router.py.
resources/lib/router.py -> Parses the plugin:// URL and calls one ui.py function.
resources/lib/ui.py      -> Builds every menu/list Kodi shows (ListItems).
resources/lib/integrations/ -> Finds + browses OTHER installed add-ons (routing only).
resources/lib/scrapers/     -> Free/legal metadata + stream sources (TMDB, archive.org, custom).
resources/lib/content/      -> Unified categories, favorites, search, import/export.
resources/lib/utils/        -> Small Kodi API wrappers (settings, JSON-RPC, cache, logging).
```

Folder layout:

```
plugin.video.meoshub/
  addon.xml
  default.py
  setup_dev.bat
  resources/
    settings.xml
    lib/
      router.py
      ui.py
      integrations/
        base.py           # Integration/IntegrationSpec classes
        known_addons.py   # Built-in specs: Scrubs V2, The Loop, Ghost, The Crew
        manager.py        # Resolves specs -> installed add-ons, merges categories
      scrapers/
        base.py           # MetadataScraper / StreamScraper interfaces
        tmdb_scraper.py   # TMDB metadata (needs a free user API key)
        archive_org_scraper.py  # Public-domain streams via archive.org
        custom_scraper.py # Generic JSON-API scraper driven by a URL template
        manager.py        # Registry of enabled scrapers
      content/
        categories.py     # Unified category list + toggles
        favorites.py       # Favorites persistence (JSON in settings)
        search.py          # Unified search across all of the above
        importexport.py    # CSV/XLSX import, JSON export
      utils/
        kodi.py, jsonrpc.py, cache.py, settings.py
  tools/
    test_harness.py    # Offline validation + smoke tests (no Kodi required)
    kodi_mocks.py       # Fake xbmc*/xbmcgui/xbmcplugin/xbmcaddon/xbmcvfs modules
```

### Main menu

`Movies | TV Shows | Networks | Sports | PPV | Live TV / Cable | Addon
Integrations | Search | Favorites | Settings`

Each unified category page shows:
- A "Search free public-domain ..." shortcut (archive.org), when enabled.
- Merged listings pulled live from every installed/enabled integration
  (each item is prefixed `[Add-on Name]` so you always know its source).

### Addon Integrations menu

Lists **Scrubs V2**, **The Loop**, **Ghost**, **The Crew**, plus **+ Add
Your Own Add-on**. Each shows whether it's currently installed on this
device. Selecting an installed integration opens its own unified
Movies/TV Shows/.../Live TV categories *inside MEOS Hub*; selecting an
item routes straight into that add-on's own `plugin://` URL, exactly like
opening it directly - MEOS Hub does not need to understand its internal
code to do this.

---

## 2. Adding a new integrated add-on

You do **not** need to edit any code to add an add-on:

1. Go to **Addon Integrations -> + Add Your Own Add-on** (or **Settings ->
   Manage Integrations -> + Add Your Own Add-on**).
2. Enter the exact add-on id (e.g. `plugin.video.example`) - find this in
   Kodi's *Add-ons -> My add-ons -> ... -> Information* screen.
3. MEOS Hub will browse that add-on's own menu tree looking for folders
   named things like "Movies", "TV Shows", "Live TV", etc. and merge
   whatever it finds into the matching MEOS Hub category. If the add-on
   uses different wording, its content still shows up as a folder shortcut
   you can browse manually inside **Addon Integrations**.

If you *are* editing code (e.g. to contribute a better path mapping for a
popular add-on), add an entry to `BUILTIN_INTEGRATIONS` in
`resources/lib/integrations/known_addons.py`:

```python
{
    'key': 'myaddon',
    'label': 'My Add-on',
    'addon_id_guess': 'plugin.video.myaddon',
    'keywords': ['myaddon', 'my add-on'],   # used for fuzzy matching if the id differs
    'category_paths': {
        'movies': [['Movies'], ['Movies', 'Movies']],
        'tvshows': [['TV Shows']],
        ...
    },
},
```
and add a matching bool setting + `BUILTIN_TOGGLE_SETTING` entry if you
want it individually toggleable like the four required integrations.

## 3. Adding a new scraper

**Without writing code:** go to **Settings -> Manage Scrapers -> + Add
Custom Scraper**, give it a name and a URL template containing `{query}`.
The endpoint must return a JSON array (or `{"results": [...]}` /
`{"items": [...]}`) of objects with any of these common field names:
`title`/`name`, `url`/`link`/`stream`, `poster`/`thumb`/`image`,
`plot`/`description`, `year`/`date`.

**With code:** subclass `MetadataScraper` or `StreamScraper` in
`resources/lib/scrapers/base.py`, implement `search(self, query)`, and
register it in `resources/lib/scrapers/manager.py`'s
`get_metadata_scrapers()` / `get_stream_scrapers()`.

## 4. Customizing menus

- **Toggle categories:** Settings -> Toggle Categories (or the native Kodi
  add-on settings screen under "Categories").
- **UI theme:** Settings -> Change UI Theme (Default/Dark/Light).
- **Category -> integration path mapping:** edit `category_paths` in
  `known_addons.py`, or use **+ Add Your Own Add-on** which relies on
  automatic folder-name matching.

## 5. Import / Export

- **Import** (Settings -> Import/Export -> Import Content Sources):
  accepts a CSV or simple single-sheet XLSX file with header row
  `title,category,type,value`, where `type` is `addon` (value = an add-on
  id to integrate) or `stream` (value = a direct playable URL, saved to
  Favorites).
- **Export**: writes JSON files (`meoshub_integrations.json`,
  `meoshub_scrapers.json`, `meoshub_favorites.json`) to the folder set in
  Settings -> Import/Export folder (default `special://temp/meoshub_exports`).

## 6. Testing

Run the offline test harness any time, no Kodi installation required:

```
python tools/test_harness.py
```

It validates `addon.xml`/`settings.xml`, byte-compiles every `.py` file,
and smoke-tests the router against every core screen using lightweight
mocks of the Kodi Python API (`tools/kodi_mocks.py`).

## 7. Dev automation script

```
setup_dev.bat            REM validate only
setup_dev.bat launch     REM validate, install into %APPDATA%\Kodi\addons, launch Kodi --debug, open kodi.log
setup_dev.bat logs       REM just open the current kodi.log
```

Set the `KODI_HOME` environment variable first if your Kodi userdata
folder isn't the default `%APPDATA%\Kodi`.

## 8. Notes on legality and scope

MEOS Hub only ships code that talks to official/public APIs
(archive.org's public metadata API, the official TMDB API using your own
free key) and routes into add-ons the user has chosen to install
separately. It does not include, scrape, or proxy any unlicensed
streaming sources.
