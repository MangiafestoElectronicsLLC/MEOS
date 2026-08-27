"""
MEOS provider stream validator.

Runs every provider catalog outside Kodi (with stubbed xbmc modules), resolves
each item to its real stream URL, and probes that URL to confirm it plays.

Usage:
    python scripts/validate_providers.py                 # test everything
    python scripts/validate_providers.py --limit 25      # cap items per provider/category
    python scripts/validate_providers.py --provider fast_channels
"""

import argparse
import json
import os
import sys
import time
import types
from concurrent.futures import ThreadPoolExecutor

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:  # Python 2 fallback
    from urllib2 import urlopen, Request, HTTPError


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON_DIR = os.path.join(REPO_ROOT, "repository.meos")
CATEGORIES = ["movies", "tv", "cable", "ppv", "docs", "sports", "live"]
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _install_kodi_stubs():
    """Minimal xbmc* stand-ins so provider modules import outside Kodi."""
    xbmc = types.ModuleType("xbmc")
    xbmc.LOGWARNING = 3
    xbmc.LOGERROR = 4
    xbmc.LOGINFO = 1
    xbmc.LOGDEBUG = 0
    xbmc.log = lambda msg, level=1: None
    xbmc.executebuiltin = lambda cmd: None

    xbmcaddon = types.ModuleType("xbmcaddon")

    class _Addon(object):
        def __init__(self, addon_id=None):
            # Provider code uses this constructor to detect installed add-ons.
            raise Exception("not installed: {}".format(addon_id))

    xbmcaddon.Addon = _Addon

    for name, module in (("xbmc", xbmc), ("xbmcaddon", xbmcaddon)):
        sys.modules[name] = module


def _safe(text):
    """Console-safe text; Windows consoles default to cp1252."""
    encoding = getattr(sys.stdout, "encoding", None) or "ascii"
    return str(text).encode(encoding, "replace").decode(encoding, "replace")


def probe(url, timeout=15, attempts=3):
    """Return (ok, detail) after fetching the first bytes of a stream URL."""
    if not url:
        return False, "empty url"
    if url.startswith("plugin://"):
        return True, "kodi plugin handoff"
    if not url.startswith("http"):
        return False, "unsupported scheme"

    # Kodi encodes request headers after a pipe; strip them for the probe.
    url = url.split("|", 1)[0]
    headers = {"User-Agent": UA, "Range": "bytes=0-4095", "Accept": "*/*"}
    detail = ""
    for attempt in range(attempts):
        try:
            resp = urlopen(Request(url, headers=headers), timeout=timeout)
            status = getattr(resp, "status", None) or resp.getcode()
            body = resp.read(4096)
        except HTTPError as exc:
            detail = "HTTP {}".format(exc.code)
            # Archive.org and CDNs throttle bursts; back off before believing a failure.
            if exc.code in (429, 500, 502, 503, 504):
                time.sleep(2 * (attempt + 1))
                continue
            return False, detail
        except Exception as exc:
            detail = type(exc).__name__ + ": " + str(exc)[:120]
            time.sleep(1 + attempt)
            continue

        if status not in (200, 206):
            return False, "HTTP {}".format(status)
        if not body:
            return False, "empty body"

        lowered = url.lower().split("?")[0]
        if lowered.endswith(".m3u8") or b"#EXTM3U" in body[:64]:
            if b"#EXTM3U" not in body:
                return False, "not a valid HLS manifest"
            if b"#EXT-X-STREAM-INF" not in body and b"#EXTINF" not in body:
                return False, "HLS manifest has no renditions"
        return True, "HTTP {}".format(status)

    return False, detail or "unreachable"


def collect(provider, limit):
    """Return de-duplicated catalog rows keyed by media_id with source categories."""
    seen = {}
    for category in CATEGORIES:
        try:
            rows = provider.get_catalog(None, category=category) or []
        except Exception as exc:
            print("  ! catalog error [{}]: {}".format(category, exc))
            continue
        if limit:
            rows = rows[:limit]
        for row in rows:
            media_id = row.get("media_id")
            if not media_id:
                continue
            entry = seen.setdefault(media_id, {"row": row, "categories": []})
            entry["categories"].append(category)
    return seen


def check_item(provider, media_id, entry):
    row = entry["row"]
    result = {
        "provider": provider.id,
        "media_id": media_id,
        "title": row.get("title", ""),
        "categories": entry["categories"],
    }
    try:
        entitled, reason = provider.check_entitlement(media_id, None)
    except Exception as exc:
        result.update(ok=False, detail="entitlement error: {}".format(exc))
        return result
    if not entitled:
        result.update(ok=True, detail="gated: {}".format(reason), skipped=True)
        return result

    try:
        playback = provider.resolve_playback(media_id, None)
    except Exception as exc:
        result.update(ok=False, detail="resolve error: {}".format(exc))
        return result
    if not playback or not playback.get("stream_url"):
        # One retry: resolution hits the source API and can be throttled.
        time.sleep(2)
        try:
            playback = provider.resolve_playback(media_id, None)
        except Exception as exc:
            result.update(ok=False, detail="resolve error: {}".format(exc))
            return result
    if not playback or not playback.get("stream_url"):
        result.update(ok=False, detail="no stream url")
        return result

    if playback.get("license_url"):
        result.update(ok=True, detail="DRM stream (license configured)", skipped=True)
        return result

    ok, detail = probe(playback["stream_url"])
    result.update(ok=ok, detail=detail, url=playback["stream_url"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="max items per provider/category (0 = all)")
    parser.add_argument("--provider", action="append", help="only test these provider ids")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--out", default=os.path.join(REPO_ROOT, "provider-validation.json"))
    args = parser.parse_args()

    _install_kodi_stubs()
    sys.path.insert(0, ADDON_DIR)
    from providers import get_providers

    all_results = []
    for provider in get_providers():
        if args.provider and provider.id not in args.provider:
            continue
        print("== {} ({})".format(provider.id, provider.name))
        catalog = collect(provider, args.limit)
        print("   {} unique items".format(len(catalog)))
        if not catalog:
            continue

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [
                pool.submit(check_item, provider, media_id, entry)
                for media_id, entry in catalog.items()
            ]
            results = [f.result() for f in futures]

        failed = [r for r in results if not r["ok"]]
        skipped = [r for r in results if r.get("skipped")]
        print("   ok={} failed={} skipped={}".format(
            len(results) - len(failed) - len(skipped), len(failed), len(skipped)))
        for r in failed[:40]:
            print("   FAIL {} | {} | {}".format(_safe(r["media_id"]), _safe(r["title"])[:50], _safe(r["detail"])))
        all_results.extend(results)

    with open(args.out, "w") as handle:
        json.dump(all_results, handle, indent=2)

    failures = [r for r in all_results if not r["ok"]]
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
