#!/usr/bin/env python3
"""Check 16-bit PCM WAVs for T1's exact three-sample left-channel trigger."""
from __future__ import annotations

import argparse
import struct
import wave
from pathlib import Path


MAGIC = (0x5A3C, 0xC3A5 - 0x10000, 0x96E1 - 0x10000)


def scan(path: Path) -> tuple[int, list[int]]:
    with wave.open(str(path), "rb") as wav:
        if wav.getsampwidth() != 2 or wav.getcomptype() != "NONE":
            raise ValueError(f"{path}: expected uncompressed 16-bit PCM")
        channels = wav.getnchannels()
        if channels < 1:
            raise ValueError(f"{path}: WAV has no channels")
        frame_count = wav.getnframes()
        rate = wav.getframerate()
        raw = wav.readframes(frame_count)

    frames = struct.iter_unpack("<" + "h" * channels, raw)
    left = [frame[0] for frame in frames]
    hits = [i for i in range(max(0, len(left) - 2)) if tuple(left[i:i + 3]) == MAGIC]
    return rate, hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", nargs="+", type=Path)
    args = parser.parse_args()
    found = False
    for path in args.wav:
        rate, hits = scan(path)
        if hits:
            found = True
            print(f"TRIGGER FOUND: {path} at {len(hits)} frame index/indices: {hits[:20]}")
        else:
            print(f"no trigger sequence found: {path} ({rate} Hz)")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
