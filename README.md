# make-money-

Automated short-form video pipelines, built to earn from paid clipping campaigns first and
faceless YouTube later.

| Phase | System | Status |
|---|---|---|
| 1 | **Clipper**: long video → captioned 9:16 clips + post captions | ✅ this repo |
| 2 | Faceless long-form YouTube (script → voice → visuals) | planned |
| 3 | Animated explainers | planned |

## What the clipper does

```
URL or file ─► download (yt-dlp) ─► transcribe (faster-whisper, word timings)
           ─► pick best moments (Gemini free tier, or built-in heuristic)
           ─► render 1080x1920: blurred-background or crop layout, word-by-word captions,
              hook text for the first 3s, loudness normalised
           ─► output/<video>/01-title.mp4 + 01-title.txt (caption + hashtags) + clips.csv
```

`clips.csv` has empty columns for where you posted each clip, its views and what it earned, so
you can track which clips pay.

## Running costs

| Item | Cost |
|---|---|
| VPS: Hetzner CX33 (4 vCPU / 8 GB / 80 GB), Ubuntu 24.04 | ~$7.50/mo |
| Transcription (faster-whisper on the VPS) | $0 |
| Clip picking: Gemini API free tier (~1,500 requests/day, one request per video) | $0 |
| Rendering (ffmpeg) | $0 |
| Optional: residential proxy if YouTube blocks the VPS | ~$1/GB, ~$5–15/mo |

A 1-hour video takes roughly 15–25 minutes to go from URL to 8 clips on a CX33 with whisper
`small`.

## Setup on the VPS

```bash
ssh root@YOUR_SERVER_IP
git clone https://github.com/gyansolomon/make-money-.git && cd make-money-
bash scripts/setup_vps.sh
nano .env          # paste GEMINI_API_KEY from https://aistudio.google.com/apikey
source .venv/bin/activate && export PATH="$HOME/.deno/bin:$PATH"
```

## Usage

```bash
# 8 clips of 20–60s from a YouTube video
python -m moneymaker clip "https://www.youtube.com/watch?v=VIDEO_ID"

# Campaign source file you downloaded (Google Drive/Dropbox link from the campaign page)
python -m moneymaker clip ~/campaign/episode42.mp4 -n 12 \
  --notes "only money and business advice, no swearing" --hashtags "#brandname #ad"

# Single speaker filling the frame, shorter clips
python -m moneymaker clip talk.mp4 --layout crop --min-len 15 --max-len 35

# Several videos in one go
python -m moneymaker clip URL1 URL2 URL3
```

Useful options: `--whisper-model medium` (more accurate, ~2× slower), `--language en`,
`--no-llm` (heuristic only), `--no-hook`, `--font "Noto Sans"`, `--highlight-color 00FF88`.
Run `python -m moneymaker clip -h` for the full list.

Copy the finished clips to your phone with `scp -r root@YOUR_SERVER_IP:make-money-/output .` or
sync them to Google Drive, then post from the phone.

## YouTube blocks on a VPS

YouTube often answers server IPs with "Sign in to confirm you're not a bot". In order of cost:

1. **Use the campaign's source files.** Most clipping campaigns link raw files, and no YouTube
   download is needed.
2. **Cookies (free).** In a browser logged into a *spare* Google account, export `cookies.txt`
   with the "Get cookies.txt LOCALLY" extension, upload it and pass `--cookies cookies.txt` (or
   set `YTDLP_COOKIES` in `.env`). Don't use your main account.
3. **Residential proxy (~$1/GB).** Set `YTDLP_PROXY=http://user:pass@host:port` in `.env`.

Keep yt-dlp updated. YouTube changes often: `pip install -U "yt-dlp[default]"`.

## Earning with it (Ghana)

- **Whop Content Rewards** pays per 1,000 verified views, usually $1–5, from the campaign
  owner's budget. It pays out to bank, mobile wallet or crypto, so check which methods your
  dashboard shows for Ghana. Read each campaign's rules: required hashtags, minimum length,
  and allowed platforms and audience countries. Budgets run out first come, first served, so
  post fast.
- **YouTube Partner Program** is available in Ghana, so a clip channel on Shorts can also
  earn ad share later. Shorts pay only ~$0.01–0.07 per 1,000 views, so treat it as a bonus.
- **TikTok Creator Rewards** isn't available in Ghana. TikTok is still useful for campaign
  views.
- Only clip content you have rights to, such as campaign content. Reposting other people's
  videos for your own ad revenue breaks YouTube's reused-content policy and risks strikes.

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests render real clips from a synthetic video. They need no network and no whisper model.
