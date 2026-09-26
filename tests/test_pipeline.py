"""End-to-end render on a synthetic video (no network, no whisper model)."""

from pathlib import Path

from moneymaker import media
from moneymaker.clipper import ClipJob, job_id, run
from tests.helpers import make_transcript


def make_video(path: Path, seconds: int = 40) -> Path:
    media.run_ffmpeg([
        "-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate=30:duration={seconds}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(path),
    ])
    return path


def test_clip_pipeline_end_to_end(tmp_path):
    video = make_video(tmp_path / "talk.mp4")
    work = tmp_path / "work"
    cache = work / job_id(str(video))
    cache.mkdir(parents=True)
    texts = ["Why do most people never get rich? Here is the truth nobody tells you."] * 2 + \
            ["and so we kept going with the rest of the conversation for a bit longer"] * 6
    make_transcript(texts).save(cache / "transcript-small.json")

    for layout in ("fit", "crop"):
        out = tmp_path / f"out-{layout}"
        results = run(ClipJob(source=str(video), out_dir=out, work_root=work, count=2,
                              min_len=8, max_len=15, layout=layout, use_llm=False), log=lambda *_: None)
        assert results
        folder = next(out.iterdir())
        for r in results:
            info = media.probe(folder / r["file"])
            assert (info["width"], info["height"]) == (1080, 1920)
            assert abs(info["duration"] - r["duration"]) < 0.5
            assert info["has_audio"]
            assert (folder / r["file"].replace(".mp4", ".txt")).read_text().strip()
        assert (folder / "clips.json").exists() and (folder / "clips.csv").exists()
