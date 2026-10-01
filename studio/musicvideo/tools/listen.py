"""Ask Gemini to listen to the song and review it (Claude can't hear audio). Needs GEMINI_API_KEY or a key-injecting proxy."""
import base64, json, os, sys, requests
path = sys.argv[1] if len(sys.argv) > 1 else "audio/song.mp3"
prompt = open(sys.argv[2]).read() if len(sys.argv) > 2 else """You are a music producer reviewing a spoken-word track for a lyric music video: a male narrator over a generated Afrobeat-style instrumental (100 BPM, bell pattern, shaker, bass, pads), telling the story of how farmers in Niger regrew 200 million trees.
Rate 1-10 and explain briefly: (1) instrumental quality and genre feel, (2) how well the narration sits on the beat, (3) mix balance (voice vs music, too loud/quiet parts), (4) any mispronunciations (names: Niger said 'nee-ZHAIR', Tony Rinaudo), (5) the arrangement's arc (the beat drops out at 'Then the rain stops', builds before 'it isn't a bush', opens up for the regrowth), (6) anything that sounds cheap, harsh, clipped or off-grid, with timestamps. Then list the 5 most important fixes, most important first. Be strict and concrete."""
hdr = {"x-goog-api-key": os.environ["GEMINI_API_KEY"]} if os.environ.get("GEMINI_API_KEY") else {}
body = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/mp3", "data": base64.b64encode(open(path, "rb").read()).decode()}}, {"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}}
for model in ("gemini-3.5-flash", "gemini-3-flash-preview"):
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse", json=body, headers=hdr, stream=True, timeout=(30, 600))
    if r.status_code != 200:
        print(model, r.status_code, r.text[:300]); continue
    out = []
    for line in r.iter_lines(decode_unicode=True):
        if line and line.startswith("data:"):
            for c in json.loads(line[5:]).get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    out.append(p.get("text", ""))
    print("".join(out)); break
