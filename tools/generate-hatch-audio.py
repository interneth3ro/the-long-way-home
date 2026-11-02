"""Deterministic original hatch Foley: mono 24 kHz / signed 16-bit PCM.

Only the Python standard library is needed. --check compares without writing;
generation creates missing files exclusively and refuses differing existing files.
"""
import argparse
import io
import math
from pathlib import Path
import struct
import wave

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets/audio/exterior_hatch"
RATE = 24000
DURATIONS = {"open": 0.6, "close": 0.7}


def wav_bytes(direction):
    duration = DURATIONS[direction]
    closing = direction == "close"
    count = round(RATE * duration)
    state, low_noise, phase = 73021, 0.0, 0.0
    samples = []
    for i in range(count):
        t = i / RATE
        # Fixed LCG, then one-pole low pass: worn low-mid friction, no hiss.
        state = (1664525 * state + 1013904223) & 0xffffffff
        low_noise += 0.075 * ((state / 2147483648 - 1) - low_noise)
        travel = math.sin(math.pi * i / (count - 1)) ** 0.7
        phase += 2 * math.pi * (115 + 12 * math.sin(math.pi * t / duration)) / RATE
        motor = (0.075 * math.sin(phase) + 0.025 * math.sin(phase * 2)
                 + 0.018 * math.sin(phase * 3)) * travel
        motor *= 0.88 + 0.12 * math.sin(2 * math.pi * 19 * t)
        friction = 0.13 * low_noise * travel

        def contact(start, strength):
            age = t - start
            if age < 0:
                return 0.0
            attack = min(1.0, age / 0.004)
            return strength * attack * math.exp(-age / 0.023) * (
                math.sin(2 * math.pi * 245 * age)
                + 0.35 * math.sin(2 * math.pi * 510 * age)
                + 0.2 * low_noise)

        unlocking = contact(0.008, 0.065 if closing else 0.12)
        latch = contact(duration - 0.085, 0.22 if closing else 0.15)
        # Smooth 10 ms outer boundaries, with explicit zero first/last samples.
        edge = min(1.0, t / 0.010, (count - 1 - i) / (RATE * 0.010))
        edge = 0.5 - 0.5 * math.cos(math.pi * edge)
        sample = (motor + friction + unlocking + latch) * edge
        assert abs(sample) < 0.5, "Unexpected synthesis headroom loss"
        samples.append(round(sample * 32767))
    result = io.BytesIO()
    with wave.open(result, "wb") as wav:
        wav.setparams((1, 2, RATE, count, "NONE", "not compressed"))
        wav.writeframes(struct.pack(f"<{count}h", *samples))
    return result.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    pairs = [(OUTPUT / f"hatch_{name}.wav", wav_bytes(name)) for name in DURATIONS]
    # Validate the entire pair before creating anything. Never replace owner data.
    for path, raw in pairs:
        if path.exists():
            if path.read_bytes() != raw:
                raise SystemExit(f"Refusing differing existing asset: {path}")
        elif args.check:
            raise SystemExit(f"Missing asset: {path}")
    if not args.check:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for path, raw in pairs:
            if not path.exists():
                with path.open("xb") as output:
                    output.write(raw)
    for path, raw in pairs:
        print(f"{path.relative_to(ROOT)}: {len(raw)} bytes; verified")


if __name__ == "__main__":
    main()
