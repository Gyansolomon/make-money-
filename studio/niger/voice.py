import json
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
SR = 24000
# (text, pause_after_seconds)
LINES = [
 ("This land was turning into desert. Today, it's covered in 200 million trees.", 0.35),
 ("And nobody planted them.", 0.7),
 ("To understand how, we have to go back about 50 years.", 0.5),
 ("South of the Sahara is a strip of land called the Sahel. Farmers have lived there for centuries, growing crops in the heat.", 0.25),
 ("And for a long time, it worked. Until people made one small decision.", 0.5),
 ("They cut down the trees. For more farmland, for firewood. Nobody thought it mattered.", 0.5),
 ("Then in the early nineteen seventies, the rain stopped.", 0.3),
 ("And that's when everyone found out what those trees had been doing all along.", 0.45),
 ("With nothing left to hold it, the wind ripped the dry soil right off the fields. Crops died. Cattle died.", 0.3),
 ("In the nineteen eighties, it happened again. Millions went hungry, and the desert kept moving south.", 0.5),
 ("So an Australian named Tony Rinaudo came to Niger to fix it. His plan was simple: plant new trees. He planted thousands.", 0.6),
 ("Almost all of them died.", 0.9),
 ("He was close to giving up. Then one day, walking through a field, he looked down at a scruffy little bush,", 0.3),
 ("and realized it wasn't a bush.", 0.7),
 ("It was a tree. Cut down years ago. And its roots were still alive underground.", 0.5),
 ("All over Niger, the old forest had never left. It was hiding under the dirt, waiting.", 0.5),
 ("So the farmers stopped planting. They picked the strongest shoot on each stump, and let it grow.", 0.5),
 ("Twenty years later, 200 million trees had come back, and the same land that was blowing away now grows enough extra food for about two and a half million people.", 0.8),
]
k = Kokoro("../models/kokoro.onnx", "../models/voices.bin")
pieces, tl, t = [], [], 0.0
for text, pause in LINES:
    a, sr = k.create(text, voice="am_liam", speed=1.05, lang="en-us")
    nz = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, nz[0]-300): nz[-1]+900]
    tl.append({"text": text, "start": round(t, 2), "end": round(t + len(a)/SR, 2)})
    pieces += [a, np.zeros(int(pause*SR), np.float32)]; t += len(a)/SR + pause
sf.write("narration.wav", np.concatenate(pieces), SR)
json.dump(tl, open("lines.json", "w"), indent=1)
print(f"total {t:.1f}s")
