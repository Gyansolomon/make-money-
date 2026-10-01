"""Download the large assets the video studio needs (kept out of git).

Run once from this folder:  python setup_assets.py

- models/kokoro.onnx, models/voices.bin   Kokoro TTS (Apache-2.0), ~350 MB
- chile/assets/world.npy                   Natural Earth NE1 shaded-relief raster as RGB numpy, ~670 MB
- chile/assets/countries.geojson           Natural Earth 50m country borders (public domain)
"""

import io
import zipfile
from pathlib import Path

import requests

HERE = Path(__file__).parent
MODELS = HERE / "models"
ASSETS = HERE / "chile" / "assets"

KOKORO = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
NE_RASTER = "https://naciscdn.org/naturalearth/10m/raster/NE1_HR_LC_SR_W_DR.zip"
NE_COUNTRIES = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
                "geojson/ne_50m_admin_0_countries.geojson")


def download(url, dest):
    if dest.exists():
        print("have", dest.name)
        return
    print("downloading", url)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        tmp.rename(dest)


def world_texture():
    dest = ASSETS / "world.npy"
    if dest.exists():
        print("have world.npy")
        return
    import cv2
    import numpy as np

    print("downloading", NE_RASTER)
    data = requests.get(NE_RASTER, timeout=600).content
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".tif"))
        tif = ASSETS / "NE1_HR_LC_SR_W_DR.tif"
        tif.write_bytes(z.read(name))
    im = cv2.cvtColor(cv2.imread(str(tif), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    np.save(dest, im)
    tif.unlink()
    print("world.npy", im.shape)


if __name__ == "__main__":
    MODELS.mkdir(exist_ok=True)
    download(KOKORO + "kokoro-v1.0.int8.onnx", MODELS / "kokoro.onnx")
    download(KOKORO + "voices-v1.0.bin", MODELS / "voices.bin")
    download(NE_COUNTRIES, ASSETS / "countries.geojson")
    world_texture()
