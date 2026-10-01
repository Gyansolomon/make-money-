"""Ask Gemini to rate candidate background-music excerpts (ex/*.mp3) for a map explainer. Needs GEMINI_API_KEY."""
import base64, json, sys, time, requests, glob, os
HEADERS = {"x-goog-api-key": os.environ["GEMINI_API_KEY"]} if os.environ.get("GEMINI_API_KEY") else {}
files = sorted(glob.glob("ex/*.mp3"))
parts = [{"text": "You are a music supervisor for fast-paced geography/history YouTube Shorts (style of 'Just Planet', 'MapLore': energetic narration over maps, low background music, whooshes). Below are 15-second excerpts of candidate background tracks. For EACH, give: label, genre, mood, tempo feel, audio quality (1-10), any vocals (yes/no), and suitability as a LOW-VOLUME bed under an energetic male narrator for a map explainer about Chile's history and geography (1-10). Then name your top 3 picks and why. Be strict: cheesy, childish, lo-quality or distracting tracks score low. Reply as compact JSON: {\"tracks\":[...],\"top3\":[...]}"}]
for f in files:
    parts.append({"text": f"Track label: {os.path.basename(f)[:-4]}"})
    parts.append({"inlineData": {"mimeType": "audio/mp3", "data": base64.b64encode(open(f, "rb").read()).decode()}})
body = {"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}
for model in ("gemini-3-flash-preview", "gemini-3.5-flash"):
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", json=body, headers=HEADERS, timeout=120)
    print(model, r.status_code)
    if r.status_code == 200:
        d = r.json(); print("usage", d.get("usageMetadata", {}).get("totalTokenCount"))
        open("music_rating.json", "w").write(d["candidates"][0]["content"]["parts"][0]["text"]); break
    print(r.text[:200]); time.sleep(10)
