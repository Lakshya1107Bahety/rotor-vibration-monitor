// Rotor vibration logger: ESP32 + MPU6050
// Samples the accelerometer at a fixed 1000 Hz and streams CSV over serial:
//   t_us,ax,ay,az      (ax/ay/az in raw counts, +/-4 g range -> 8192 counts/g)
//
// Wiring: MPU6050 VCC->3V3, GND->GND, SDA->GPIO21, SCL->GPIO22

#include <Wire.h>

const uint8_t MPU_ADDR      = 0x68;
const uint32_t SAMPLE_US    = 1000;      // 1000 Hz sample rate
const uint32_t SERIAL_BAUD  = 921600;

void mpuWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  Wire.begin(21, 22);
  Wire.setClock(400000);               // fast-mode I2C, needed for 1 kHz reads

  mpuWrite(0x6B, 0x00);                // PWR_MGMT_1: wake up, internal clock
  delay(100);
  mpuWrite(0x1A, 0x02);                // CONFIG: DLPF ~94 Hz accel bandwidth
  mpuWrite(0x19, 0x00);                // SMPLRT_DIV: 1 kHz internal sample rate
  mpuWrite(0x1C, 0x08);                // ACCEL_CONFIG: +/-4 g

  Serial.println("t_us,ax,ay,az");
}

void loop() {
  static uint32_t next = micros();
  // Busy-wait for the next sample slot so the sample interval stays constant.
  // A constant interval matters more than raw speed: the FFT assumes it.
  while ((int32_t)(micros() - next) < 0) {}
  uint32_t t = micros();
  next += SAMPLE_US;

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);                    // ACCEL_XOUT_H
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, (uint8_t)6);
  int16_t ax = (Wire.read() << 8) | Wire.read();
  int16_t ay = (Wire.read() << 8) | Wire.read();
  int16_t az = (Wire.read() << 8) | Wire.read();

  Serial.print(t);  Serial.print(',');
  Serial.print(ax); Serial.print(',');
  Serial.print(ay); Serial.print(',');
  Serial.println(az);
}
