#!/usr/bin/env python3
"""Generate a WAV showing T1s short bypass pulse and automatic FIR recovery."""
from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path


MAGIC = (0x5A3C, 0xC3A5 - 0x10000, 0x96E1 - 0x10000)


def make_samples(rate: int, tone_hz: float, tone_seconds: float, amplitude: int) -> list[int]:
    if not 0 < tone_hz < rate / 2:
        raise ValueError("tone frequency must be below Nyquist")
    if not 0 < amplitude <= 32767:
        raise ValueError("amplitude must be in 1..32767")

    # Start with pass-band audio, send the exact trigger, then hold a stop-band tone.
    # The trigger-completing frame is pulse frame one, so 127 tone frames pass before FIR filtering resumes.
    passband_count = rate // 2
    samples = [round(5000 * math.sin(2.0 * math.pi * 440.0 * n / rate))
               for n in range(passband_count)]
    samples.extend(MAGIC)
    tone_count = round(rate * tone_seconds)
    samples.extend(round(amplitude * math.sin(2.0 * math.pi * tone_hz * n / rate))
                   for n in range(tone_count))
    samples.extend([0] * 128)
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="destination 16-bit mono WAV")
    parser.add_argument("--rate", type=int, default=16000)
    parser.add_argument("--tone-hz", type=float, default=4800.0)
    parser.add_argument("--tone-seconds", type=float, default=0.75)
    parser.add_argument("--amplitude", type=int, default=12000)
    args = parser.parse_args()

    samples = make_samples(args.rate, args.tone_hz, args.tone_seconds, args.amplitude)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(args.output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(args.rate)
        wav.writeframes(b"".join(struct.pack("<h", x) for x in samples))
    print(f"wrote {len(samples)} samples at {args.rate} Hz to {args.output}")


if __name__ == "__main__":
    main()
