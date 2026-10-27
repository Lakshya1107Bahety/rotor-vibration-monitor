"""Generate synthetic vibration data to test the analysis pipeline before hardware runs.

Signal model (a 3-blade table fan):
  - 1x rotation component (small when balanced, large when a mass is added to a blade)
  - 3x blade-pass component
  - 100 Hz motor hum (2x the 50 Hz mains frequency)
  - gravity offset on z, plus white noise

This is SIMULATED data. It checks that the code works, not that the method works on a real fan.
"""
import numpy as np
import pandas as pd
from pathlib import Path

FS = 1000           # Hz
COUNTS_PER_G = 8192


def make_run(seconds, rot_hz, imbalance_g, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * FS)) / FS
    phase = rng.uniform(0, 2 * np.pi, 3)
    one_x = imbalance_g * np.sin(2 * np.pi * rot_hz * t + phase[0])
    bpf = 0.02 * np.sin(2 * np.pi * 3 * rot_hz * t + phase[1])
    hum = 0.01 * np.sin(2 * np.pi * 100 * t + phase[2])
    noise = lambda: rng.normal(0, 0.015, t.size)
    ax = one_x + bpf + hum + noise()
    ay = 0.6 * one_x + 0.5 * bpf + noise()
    az = 1.0 + 0.2 * bpf + noise()
    df = pd.DataFrame({
        "t_us": (t * 1e6).astype(np.int64),
        "ax": (ax * COUNTS_PER_G).astype(int),
        "ay": (ay * COUNTS_PER_G).astype(int),
        "az": (az * COUNTS_PER_G).astype(int),
    })
    return df


def main():
    out = Path(__file__).resolve().parent.parent / "data" / "simulated"
    out.mkdir(parents=True, exist_ok=True)
    seed = 0
    for speed, rot_hz in [(1, 15.0), (2, 18.5), (3, 21.0)]:
        for run in range(1, 4):
            seed += 1
            hz = rot_hz * np.random.default_rng(seed).uniform(0.98, 1.02)
            make_run(30, hz, 0.01, seed).to_csv(out / f"normal_speed{speed}_run{run}.csv", index=False)
            seed += 1
            make_run(30, hz, 0.08, seed).to_csv(out / f"imbalance_speed{speed}_run{run}.csv", index=False)
    print(f"wrote simulated runs to {out}")


if __name__ == "__main__":
    main()
