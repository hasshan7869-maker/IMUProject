/*
  BLE IMU Streamer (with connection interval tuning)
  -----------------------------------------------------
  Same as the diagnostic version, but now explicitly requests a fast
  BLE connection interval (7.5-15ms) right when a device connects,
  instead of relying on Windows' default negotiation. This should
  let far more of the 50Hz notify() calls actually get through.
*/

#include <Wire.h>
#include "SparkFun_BMI270_Arduino_Library.h"
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

BMI270 imu;
uint8_t i2cAddress = BMI2_I2C_PRIM_ADDR;

BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

unsigned long startTime;

uint32_t notifyCount = 0;
unsigned long lastReportTime = 0;

#pragma pack(push, 1)
struct ImuPacket {
  uint32_t timestamp_ms;
  int16_t accelX_mg;
  int16_t accelY_mg;
  int16_t accelZ_mg;
  int16_t gyroX_dps10;
  int16_t gyroY_dps10;
  int16_t gyroZ_dps10;
};
#pragma pack(pop)

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer, esp_ble_gatts_cb_param_t* param) {
      deviceConnected = true;
      Serial.println("Device connected! Requesting fast connection interval...");

      // Request: min 6 (7.5ms), max 12 (15ms), latency 0, timeout 400 (4s)
      pServer->updateConnParams(param->connect.remote_bda, 6, 12, 0, 400);

      notifyCount = 0;
      lastReportTime = millis();
    }

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      Serial.println("Device disconnected, restarting advertising...");
      pServer->getAdvertising()->start();
    }
};

void setupBMI270() {
  Wire.begin();

  while (imu.beginI2C(i2cAddress) != BMI2_OK) {
    Serial.println("Error: BMI270 not connected, check wiring!");
    delay(1000);
  }
  Serial.println("BMI270 connected!");

  int8_t err = BMI2_OK;

  bmi2_sens_config accelConfig;
  accelConfig.type = BMI2_ACCEL;
  accelConfig.cfg.acc.odr = BMI2_ACC_ODR_100HZ;
  accelConfig.cfg.acc.bwp = BMI2_ACC_OSR4_AVG1;
  accelConfig.cfg.acc.filter_perf = BMI2_PERF_OPT_MODE;
  accelConfig.cfg.acc.range = BMI2_ACC_RANGE_16G;
  err = imu.setConfig(accelConfig);

  bmi2_sens_config gyroConfig;
  gyroConfig.type = BMI2_GYRO;
  gyroConfig.cfg.gyr.odr = BMI2_GYR_ODR_100HZ;
  gyroConfig.cfg.gyr.bwp = BMI2_GYR_OSR4_MODE;
  gyroConfig.cfg.gyr.filter_perf = BMI2_PERF_OPT_MODE;
  gyroConfig.cfg.gyr.ois_range = BMI2_GYR_OIS_250;
  gyroConfig.cfg.gyr.range = BMI2_GYR_RANGE_2000;
  gyroConfig.cfg.gyr.noise_perf = BMI2_PERF_OPT_MODE;
  err = imu.setConfig(gyroConfig);

  while (err != BMI2_OK) {
    Serial.print("BMI270 config error: ");
    Serial.println(err);
    delay(1000);
  }

  Serial.println("BMI270 config valid!");
}

void setupBLE() {
  BLEDevice::init("IMU_Wearable");

  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);

  // Advertise a preference for a fast connection interval too
  pAdvertising->setMinPreferred(0x06);  // 7.5ms
  pAdvertising->setMaxPreferred(0x0C);  // 15ms

  BLEDevice::startAdvertising();

  Serial.println("BLE advertising started as 'IMU_Wearable'.");
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE IMU Streamer (fast connection interval)...");

  setupBMI270();
  setupBLE();

  startTime = millis();
  lastReportTime = millis();
}

void loop() {
  static unsigned long lastSend = 0;
  const unsigned long sendIntervalMs = 20; // back to ~50Hz target now that we're tuning the interval

  if (deviceConnected && millis() - lastSend >= sendIntervalMs) {
    lastSend = millis();

    imu.getSensorData();

    ImuPacket packet;
    packet.timestamp_ms = millis() - startTime;
    packet.accelX_mg = (int16_t)(imu.data.accelX * 1000.0);
    packet.accelY_mg = (int16_t)(imu.data.accelY * 1000.0);
    packet.accelZ_mg = (int16_t)(imu.data.accelZ * 1000.0);
    packet.gyroX_dps10 = (int16_t)(imu.data.gyroX * 10.0);
    packet.gyroY_dps10 = (int16_t)(imu.data.gyroY * 10.0);
    packet.gyroZ_dps10 = (int16_t)(imu.data.gyroZ * 10.0);

    pCharacteristic->setValue((uint8_t*)&packet, sizeof(packet));
    pCharacteristic->notify();

    notifyCount++;
  }

  if (deviceConnected && millis() - lastReportTime >= 1000) {
    float actualRateHz = notifyCount / ((millis() - lastReportTime) / 1000.0);
    Serial.print("Notify calls in last interval: ");
    Serial.print(notifyCount);
    Serial.print("  |  actual send rate: ");
    Serial.print(actualRateHz, 1);
    Serial.println(" Hz");

    notifyCount = 0;
    lastReportTime = millis();
  }
}
