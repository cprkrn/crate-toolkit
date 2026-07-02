#!/usr/bin/env python3
"""Spot "fake lossless" files — AIFF/WAV/FLAC that are really a lossy source
(MP3 / YouTube rip) upconverted into a lossless container.

How: decode a slice of each file and measure the high-frequency cutoff. Genuine
lossless has real energy out to ~21-22 kHz; a lossy transcode drops off a cliff
earlier (320 MP3 ~20 kHz, 256 ~19 kHz, 128 ~16 kHz). A low cutoff strongly
suggests a lossy source — BUT a genuinely dark/mellow master can also read low,
so treat flags as candidates to verify by ear.

Needs: ffmpeg on PATH, numpy. Reads file paths from your rekordbox library
(lossless only) by default, or pass --dir to scan a folder of audio files.

Run:  python aiff_quality_audit.py [--dir /path/to/audio] [--ext aiff,wav,flac]
"""
import argparse, os, subprocess, sys
import numpy as np

LOSSLESS = ("aiff", "aif", "wav", "flac")


def cutoff_khz(path):
    for ss, t in (("45", "15"), ("0", "20")):
        raw = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-vn", "-ss", ss, "-t", t,
             "-i", path, "-ac", "1", "-ar", "44100", "-f", "f32le", "-"],
            capture_output=True).stdout
        x = np.frombuffer(raw, dtype=np.float32)
        if len(x) >= 44100 * 3:
            break
    else:
        return None
    N = 16384
    win = np.hanning(N)
    frames = len(x) // N
    if frames < 1:
        return None
    acc = np.zeros(N // 2 + 1)
    for i in range(frames):
        acc += np.abs(np.fft.rfft(x[i * N:(i + 1) * N] * win))
    acc /= frames
    freqs = np.fft.rfftfreq(N, 1 / 44100)
    db = 20 * np.log10(acc + 1e-12)
    db -= db.max()
    above = np.where(db > -80)[0]
    return round(float(freqs[above[-1]] / 1000), 1) if len(above) else 0.0


def collect(args):
    if args.dir:
        exts = tuple(e.strip().lower() for e in args.ext.split(","))
        out = []
        for root, _, files in os.walk(args.dir):
            for f in files:
                if f.rsplit(".", 1)[-1].lower() in exts:
                    out.append((f, os.path.join(root, f)))
        return out
    from pyrekordbox import Rekordbox6Database
    db = Rekordbox6Database()
    out = []
    for c in db.get_content():
        fp = getattr(c, "FolderPath", "") or ""
        if fp.rsplit(".", 1)[-1].lower() in LOSSLESS:
            ar = (c.Artist.Name if getattr(c, "Artist", None) else "") or ""
            out.append((f"{ar} - {c.Title}", fp))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="scan a folder instead of the rekordbox library")
    ap.add_argument("--ext", default="aiff,aif,wav,flac")
    args = ap.parse_args()
    files = collect(args)
    print(f"analyzing {len(files)} lossless files...\n")
    res = []
    for label, path in files:
        try:
            res.append((cutoff_khz(path), label))
        except Exception:
            res.append((None, label))
    genuine = [r for r in res if r[0] and r[0] >= 21]
    borderline = [r for r in res if r[0] and 19 <= r[0] < 21]
    lossy = [r for r in res if r[0] is not None and r[0] < 19]
    fail = [r for r in res if r[0] is None]
    print(f"  genuine lossless (>=21kHz): {len(genuine)}")
    print(f"  borderline (19-21kHz, often just natural rolloff): {len(borderline)}")
    print(f"  likely LOSSY transcode (<19kHz): {len(lossy)}")
    print(f"  failed/missing: {len(fail)}")
    if lossy:
        print("\n-- likely lossy (verify by ear) --")
        for cut, label in sorted(lossy):
            print(f"   {cut}kHz  {label}")


if __name__ == "__main__":
    main()
