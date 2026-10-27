# Rotor Vibration Monitor

Detecting imbalance in a rotating machine from vibration data, using an ESP32 and an MPU6050 accelerometer.

Vibration monitoring is one of the main ways rotating machinery, including jet engines, is checked for developing faults. An imbalanced rotor produces a vibration peak at its rotation frequency (the "1x" component). This project is a small-scale version: a table fan is the rotor, and a small mass taped to one blade is the fault.

## Status

| Part | Status |
|---|---|
| ESP32 firmware (1 kHz fixed-rate sampling) | Written, hardware testing in progress |
| Serial capture script | Written, hardware testing in progress |
| Spectrum analysis (Welch PSD) | Working, tested on simulated data |
| Anomaly detection (Isolation Forest) | Working, tested on simulated data |
| Real fan measurements | **Not done yet** |

Everything below the firmware has only been tested on **simulated** signals so far. Real-fan results will be added once collected.

## How it works

```
MPU6050 --I2C 400 kHz--> ESP32 --serial 921600 baud--> capture.py --> CSV
                                                                     |
                                       fft_analysis.py  <------------+
                                       anomaly_detect.py <-----------+
```

1. **Firmware** samples the accelerometer every 1000 µs using a busy-wait timer, so the sample interval stays constant (the FFT assumes this).
2. **fft_analysis.py** computes a Welch-averaged power spectrum and reports the sample rate and timing jitter, so bad recordings are caught.
3. **anomaly_detect.py** splits recordings into 1-second windows and extracts 4 physically meaningful features: RMS, 1x rotation peak, blade-pass (3x) peak, and the 1x / blade-pass ratio. An Isolation Forest is trained **only on normal runs**, because in practice you rarely have data from a broken machine.

## Simulated results

The simulator models a 3-blade fan: a 1x rotation component, a 3x blade-pass component, 100 Hz motor hum (2 × 50 Hz mains), and noise.

![Simulated spectrum](docs/simulated_spectrum.png)

On held-out simulated runs: imbalance detected in all windows, with a 10% false alarm rate on normal windows.

These numbers only show that the code works. The simulated fault is clean and easy to separate, so they say nothing about how well this would work on a real fan.

## Hardware

- ESP32 dev board
- MPU6050 module, wiring: VCC→3V3, GND→GND, SDA→GPIO21, SCL→GPIO22
- Table fan, with the sensor fixed rigidly to the motor housing

## Run it

```bash
pip install -r requirements.txt
cd analysis

# test the pipeline without hardware
python simulate.py
python fft_analysis.py ../data/simulated/normal_speed2_run1.csv ../data/simulated/imbalance_speed2_run1.csv
python anomaly_detect.py ../data/simulated

# with hardware (flash firmware/vibration_logger first)
python capture.py --port COM5 --seconds 30 --out ../data/normal_speed2_run1.csv
```

## Next steps

- Record real runs: 3 fan speeds × 3 runs each, with and without the added mass
- Check the real sample-rate jitter from the ESP32
- Test whether the detector still works across fan speeds, where the 1x frequency moves
- Compare sensor mounting positions
