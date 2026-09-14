#include <Wire.h>
#include "SparkFun_BMI270_Arduino_Library.h"

BMI270 imu;
uint8_t i2cAddress = BMI2_I2C_PRIM_ADDR; // 0x68

unsigned long startTime;

void setup()
{
    Serial.begin(115200);
    Serial.println("BMI270 - Soccer Wearable Acquisition");

    Wire.begin();

    while (imu.beginI2C(i2cAddress) != BMI2_OK)
    {
        Serial.println("Error: BMI270 not connected, check wiring!");
        delay(1000);
    }
    Serial.println("BMI270 connected!");

    int8_t err = BMI2_OK;

    // Accelerometer config: +/-16g, 200Hz, performance mode
    bmi2_sens_config accelConfig;
    accelConfig.type = BMI2_ACCEL;
    accelConfig.cfg.acc.odr = BMI2_ACC_ODR_200HZ;
    accelConfig.cfg.acc.bwp = BMI2_ACC_OSR4_AVG1;
    accelConfig.cfg.acc.filter_perf = BMI2_PERF_OPT_MODE;
    accelConfig.cfg.acc.range = BMI2_ACC_RANGE_16G;
    err = imu.setConfig(accelConfig);

    // Gyroscope config: +/-2000dps, 200Hz, performance mode
    bmi2_sens_config gyroConfig;
    gyroConfig.type = BMI2_GYRO;
    gyroConfig.cfg.gyr.odr = BMI2_GYR_ODR_200HZ;
    gyroConfig.cfg.gyr.bwp = BMI2_GYR_OSR4_MODE;
    gyroConfig.cfg.gyr.filter_perf = BMI2_PERF_OPT_MODE;
    gyroConfig.cfg.gyr.ois_range = BMI2_GYR_OIS_250;
    gyroConfig.cfg.gyr.range = BMI2_GYR_RANGE_2000;
    gyroConfig.cfg.gyr.noise_perf = BMI2_PERF_OPT_MODE;
    err = imu.setConfig(gyroConfig);

    while (err != BMI2_OK)
    {
        if (err == BMI2_E_ACC_INVALID_CFG) Serial.println("Accel config invalid!");
        else if (err == BMI2_E_GYRO_INVALID_CFG) Serial.println("Gyro config invalid!");
        else if (err == BMI2_E_ACC_GYR_INVALID_CFG) Serial.println("Both configs invalid!");
        else { Serial.print("Unknown config error: "); Serial.println(err); }
        delay(1000);
    }

    Serial.println("Config valid! Starting acquisition.");
    Serial.println("timestamp_ms,accelX,accelY,accelZ,gyroX,gyroY,gyroZ");

    startTime = millis();
}

void loop()
{
    imu.getSensorData();

    unsigned long t = millis() - startTime;

    Serial.print(t);
    Serial.print(",");
    Serial.print(imu.data.accelX, 4);
    Serial.print(",");
    Serial.print(imu.data.accelY, 4);
    Serial.print(",");
    Serial.print(imu.data.accelZ, 4);
    Serial.print(",");
    Serial.print(imu.data.gyroX, 3);
    Serial.print(",");
    Serial.print(imu.data.gyroY, 3);
    Serial.print(",");
    Serial.println(imu.data.gyroZ, 3);

    delay(5); // ~200Hz to match sensor ODR
}