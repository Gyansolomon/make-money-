"""Search Freesound for CC0 sounds (scrapes the public search page, no API key). Usage: python freesound_search.py whoosh 0.2,3"""
import re, sys, json, time, requests, html
def search(q, dur=None, n=6):
    f = 'license:"Creative Commons 0"' + (f" duration:[{dur[0]} TO {dur[1]}]" if dur else "")
    r = requests.get("https://freesound.org/search/", params={"q": q, "f": f, "s": "Downloads (most first)"}, timeout=30)
    out = []
    for m in re.finditer(r'aria-label="Sound (.*?) by (.*?)">.*?data-sound-id="(\d+)".*?data-mp3="([^"]+)".*?data-duration="([\d.]+)"', r.text, re.S):
        title, user, sid, mp3, d = m.groups()
        out.append({"q": q, "id": sid, "title": html.unescape(title), "user": html.unescape(user), "mp3": mp3.replace("-lq.mp3", "-hq.mp3"), "dur": float(d)})
    return out[:n]
if __name__ == "__main__":
    q = sys.argv[1]; dur = tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    for s in search(q, dur): print(json.dumps(s))
