import json
import urllib.request as u
import urllib.parse as p

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

IDS = [
    "night_of_the_living_dead",
    "DuckandC1951",
    "nazi_concentration_camps",
    "his_girl_friday",
    "reefer_madness1938",
    "TheGeneral_201409",
    "CC_1916_05_15_TheFloorwalker",
    "Plan_9_from_Outer_Space_1959",
    "popeye_patriotic_popeye",
    "PrelingerAmericanLifestyles",
]


def get(url, read=400):
    r = u.urlopen(u.Request(url, headers={"User-Agent": UA, "Range": "bytes=0-2047"}), timeout=30)
    return r.getcode(), r.read(read)


for ident in IDS:
    try:
        r = u.urlopen(u.Request("https://archive.org/metadata/" + ident, headers={"User-Agent": UA}), timeout=30)
        meta = json.loads(r.read())
    except Exception as exc:
        print("META ERR", ident, str(exc)[:40])
        continue
    files = meta.get("files") or []
    mp4 = [f for f in files if (f.get("name") or "").lower().endswith(".mp4")]
    if not mp4:
        print("NO MP4", ident)
        continue
    mp4.sort(key=lambda f: int(f.get("size") or 0))
    name = mp4[len(mp4) // 2]["name"]
    url = "https://archive.org/download/{}/{}".format(ident, p.quote(name, safe=".-_~()"))
    title = (meta.get("metadata") or {}).get("title", ident)
    try:
        code, body = get(url)
        print("OK" if code in (200, 206) else code, "|", title[:40], "|", url)
    except Exception as exc:
        print("PROBE ERR", ident, str(exc)[:40])
