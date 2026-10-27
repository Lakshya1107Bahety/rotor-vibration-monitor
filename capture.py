"""Record N seconds of ESP32 vibration data to a CSV file.

Usage:
    python capture.py --port COM5 --seconds 30 --out ../data/normal_speed2_run1.csv
"""
import argparse
import time
import serial


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", required=True, help="e.g. COM5 or /dev/ttyUSB0")
    p.add_argument("--baud", type=int, default=921600)
    p.add_argument("--seconds", type=float, default=30)
    p.add_argument("--out", required=True)
    a = p.parse_args()

    with serial.Serial(a.port, a.baud, timeout=1) as ser, open(a.out, "w") as f:
        ser.reset_input_buffer()
        f.write("t_us,ax,ay,az\n")
        end = time.time() + a.seconds
        n = 0
        while time.time() < end:
            line = ser.readline().decode(errors="ignore").strip()
            parts = line.split(",")
            if len(parts) == 4 and parts[0].isdigit():   # skip header / garbled lines
                f.write(line + "\n")
                n += 1
    print(f"saved {n} samples to {a.out}")


if __name__ == "__main__":
    main()
