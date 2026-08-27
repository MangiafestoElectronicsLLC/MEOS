import json
import urllib.request as u

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

FEEDS = {
    "SamsungTVPlus": "https://i.mjh.nz/SamsungTVPlus/.channels.json",
    "Plex": "https://i.mjh.nz/Plex/.channels.json",
    "Roku": "https://i.mjh.nz/Roku/.channels.json",
    "PlutoTV": "https://i.mjh.nz/PlutoTV/.channels.json",
}


def get(url, headers=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    r = u.urlopen(u.Request(url, headers=h), timeout=30)
    return r.getcode(), r.geturl(), r.read(200)


for name, feed in FEEDS.items():
    r = u.urlopen(u.Request(feed, headers={"User-Agent": UA}), timeout=30)
    d = json.loads(r.read())
    slug = d.get("slug")
    headers = d.get("headers") or {}
    channels = d.get("channels")
    if channels is None:
        region = d["regions"].get("us") or list(d["regions"].values())[0]
        channels = region.get("channels") or {}
        headers = region.get("headers") or headers
    cid = list(channels)[0]
    print("== {} slug={} channels={} headers={}".format(name, slug, len(channels), headers))
    if not slug:
        continue
    url = "https://jmp2.uk/{}.m3u8".format(slug.replace("{id}", cid))
    for hdrs in (None, headers):
        try:
            code, final, body = get(url, hdrs)
            print("   OK", code, url, "->", final[:60], body[:25])
            break
        except Exception as exc:
            print("   ERR", str(exc)[:45], url, "hdrs=", bool(hdrs))
