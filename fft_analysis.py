"""Plot the averaged spectrum of one or more vibration recordings.

Usage:
    python fft_analysis.py ../data/normal_speed2_run1.csv ../data/imbalance_speed2_run1.csv
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import welch

COUNTS_PER_G = 8192


def load(path):
    df = pd.read_csv(path)
    dt = np.diff(df["t_us"].values) / 1e6
    fs = 1.0 / np.median(dt)
    jitter = np.std(dt) / np.median(dt) * 100
    ax = (df["ax"].values - df["ax"].mean()) / COUNTS_PER_G   # remove DC / gravity
    return ax, fs, jitter


def main(paths):
    plt.figure(figsize=(10, 5))
    for p in paths:
        ax, fs, jitter = load(p)
        # Welch averaging: many 1-second FFTs averaged together -> much less noisy spectrum
        f, pxx = welch(ax, fs=fs, nperseg=int(fs))
        peak = f[np.argmax(pxx[1:]) + 1]
        print(f"{Path(p).name}: fs={fs:.1f} Hz, timing jitter={jitter:.2f}%, "
              f"strongest peak={peak:.1f} Hz, RMS={np.sqrt(np.mean(ax**2))*1000:.1f} mg")
        plt.semilogy(f, pxx, label=Path(p).stem)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("PSD (g$^2$/Hz)")
    plt.title("X-axis vibration spectrum")
    plt.xlim(0, 200)
    plt.grid(True, which="both", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    out = Path(paths[0]).resolve().parent / "spectrum.png"
    plt.savefig(out, dpi=150)
    print(f"saved {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
