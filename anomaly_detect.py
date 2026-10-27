"""Imbalance detection: train only on NORMAL runs, then flag anything that looks different.

Files must be named normal_*.csv or imbalance_*.csv. Every *_run3.csv file is held out for testing.

Usage:
    python anomaly_detect.py ../data/simulated
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import welch
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix

COUNTS_PER_G = 8192
WIN_S = 1.0     # 1-second analysis windows


def features(window, fs):
    """Physically meaningful features, not black-box ones."""
    x = window - window.mean()
    f, p = welch(x, fs=fs, nperseg=len(x) // 2)
    band = (f > 5) & (f < 40)                 # where 1x rotation lives for a table fan
    i1x = np.argmax(p * band)                  # rotation peak, found automatically
    f1x = f[i1x]
    def amp(freq):                             # peak power near a given frequency
        m = np.abs(f - freq) < 1.5
        return p[m].max() if m.any() else 0.0
    return [
        np.sqrt(np.mean(x ** 2)),              # overall RMS
        np.log10(amp(f1x) + 1e-12),            # 1x (imbalance shows up here)
        np.log10(amp(3 * f1x) + 1e-12),        # blade-pass
        np.log10(amp(f1x) + 1e-12) - np.log10(amp(3 * f1x) + 1e-12),  # 1x relative to blade-pass
    ]


def windows_from(path):
    df = pd.read_csv(path)
    fs = 1e6 / np.median(np.diff(df["t_us"].values))
    ax = df["ax"].values / COUNTS_PER_G
    n = int(WIN_S * fs)
    return [features(ax[i:i + n], fs) for i in range(0, len(ax) - n + 1, n)]


def main(folder):
    files = sorted(Path(folder).glob("*.csv"))
    train, test_X, test_y = [], [], []
    for fp in files:
        is_normal = fp.name.startswith("normal")
        held_out = fp.stem.endswith("run3")
        w = windows_from(fp)
        if is_normal and not held_out:
            train += w
        elif held_out:
            test_X += w
            test_y += [0 if is_normal else 1] * len(w)

    scaler = StandardScaler().fit(train)
    model = IsolationForest(n_estimators=200, contamination=0.02, random_state=0)
    model.fit(scaler.transform(train))
    pred = (model.predict(scaler.transform(test_X)) == -1).astype(int)

    cm = confusion_matrix(test_y, pred, labels=[0, 1])
    tn, fp_, fn, tp = cm.ravel()
    print(f"trained on {len(train)} normal windows, tested on {len(test_y)} held-out windows")
    print("confusion matrix [rows: true normal/imbalance, cols: predicted normal/imbalance]")
    print(cm)
    print(f"detection rate: {tp/(tp+fn):.1%}   false alarm rate: {fp_/(fp_+tn):.1%}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
