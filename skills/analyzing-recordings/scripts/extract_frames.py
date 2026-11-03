#!/usr/bin/env python3
"""Extracts the frames of a screen recording where the screen changes, so a
recording can be looked at as a handful of images instead of every frame.

Usage: python3 -I extract_frames.py <video> <out_dir> [--max N] [--width PX] [--threshold T]

- Keeps the first frame and every frame whose scene-change score is above the
  threshold (default 0.08: a new screen, a dialog, a toast, a typed value).
- More frames than --max (default 16): keeps an evenly spaced subset, always
  with the first and the last one.
- Fewer than 3 frames from a recording longer than 3 s (a quiet recording, a
  small change): samples evenly instead.
- Scales frames down to --width (default 1280) when wider, which keeps each
  image small when it is read.

Writes frame-01-t0.0s.png, frame-02-t3.4s.png, ... into out_dir and prints one
line per frame: its path and the second of the recording it shows. Needs
ffmpeg and ffprobe on PATH.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

PTS_TIME = re.compile(r"pts_time:\s*([0-9.]+)")


def video_duration(video: Path) -> float:
    """Returns the recording's length in seconds, or 0.0 when ffprobe can't tell."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def run_ffmpeg(video: Path, out_dir: Path, select_filter: str, width: int) -> list[float]:
    """Writes the selected frames as raw-NNN.png and returns their timestamps in order."""
    scale_filter = f"scale='min({width},iw)':-2"
    command = [
        "ffmpeg", "-hide_banner", "-y", "-i", str(video),
        "-vf", f"{select_filter},showinfo,{scale_filter}",
        "-fps_mode", "vfr", str(out_dir / "raw-%03d.png"),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{result.stderr[-2000:]}")
    timestamps = []
    for line in result.stderr.splitlines():
        if "showinfo" in line:
            match = PTS_TIME.search(line)
            if match:
                timestamps.append(float(match.group(1)))
    return timestamps


def evenly_spaced(count: int, keep: int) -> list[int]:
    """Indexes of `keep` items spread over `count`, including the first and the last."""
    if count <= keep:
        return list(range(count))
    if keep == 1:
        return [0]
    step = (count - 1) / (keep - 1)
    return sorted({round(i * step) for i in range(keep)})


def clear_raw_frames(out_dir: Path) -> None:
    for path in out_dir.glob("raw-*.png"):
        path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--max", type=int, default=16, help="most frames to keep (default 16)")
    parser.add_argument("--width", type=int, default=1280, help="largest frame width in px (default 1280)")
    parser.add_argument("--threshold", type=float, default=0.08, help="scene-change score 0-1 (default 0.08)")
    args = parser.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            sys.exit(f"{tool} is not installed (macOS: brew install ffmpeg).")
    if not args.video.is_file():
        sys.exit(f"No such file: {args.video}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    clear_raw_frames(args.out_dir)

    duration = video_duration(args.video)
    scene_filter = f"select='eq(n\\,0)+gt(scene\\,{args.threshold})'"
    timestamps = run_ffmpeg(args.video, args.out_dir, scene_filter, args.width)

    if len(timestamps) < 3 and duration > 3:
        clear_raw_frames(args.out_dir)
        fps = min(args.max, 12) / duration
        timestamps = run_ffmpeg(args.video, args.out_dir, f"fps={fps:.6f}", args.width)
        print(f"Few scene changes; sampled evenly instead ({len(timestamps)} frames).")

    raw_frames = sorted(args.out_dir.glob("raw-*.png"))
    timestamps = (timestamps + [0.0] * len(raw_frames))[: len(raw_frames)]
    kept_indexes = evenly_spaced(len(raw_frames), args.max)

    print(f"Recording: {args.video} ({duration:.1f} s), {len(raw_frames)} frames extracted, {len(kept_indexes)} kept.")
    for number, index in enumerate(kept_indexes, start=1):
        target = args.out_dir / f"frame-{number:02d}-t{timestamps[index]:.1f}s.png"
        raw_frames[index].rename(target)
        print(f"{target}\t{timestamps[index]:.1f} s")
    clear_raw_frames(args.out_dir)


if __name__ == "__main__":
    main()
