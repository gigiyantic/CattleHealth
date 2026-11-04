/*
 * CattleHealth AI — ESP32 farm gateway
 * Listens for tag adverts (see docs/BLE_PAYLOAD.md), de-duplicates the 3 bursts,
 * buffers readings and uploads them as JSON to the cloud every minute.
 *
 * Board: any ESP32 / ESP32-C3 (Arduino core 3.x)
 * Libraries: NimBLE-Arduino (>= 2.0), ArduinoJson (>= 7)
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <NimBLEDevice.h>
#include <ArduinoJson.h>
#include <time.h>
#include "config.h"

struct Reading {
  uint32_t tagId; uint16_t seq; int16_t tempCenti; uint8_t rum;
  uint16_t act; uint16_t battMv; uint8_t flags; int8_t rssi; time_t ts;
};

static Reading batch[MAX_BATCH];
static volatile size_t batchLen = 0;
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

// last sequence per tag to drop the duplicate bursts
struct Seen { uint32_t tag; uint16_t seq; };
static Seen seen[64];
static size_t seenLen = 0;

static bool isDuplicate(uint32_t tag, uint16_t seq) {
  for (size_t i = 0; i < seenLen; i++) {
    if (seen[i].tag == tag) {
      if (seen[i].seq == seq) return true;
      seen[i].seq = seq;
      return false;
    }
  }
  if (seenLen < 64) seen[seenLen++] = { tag, seq };
  return false;
}

static inline uint16_t rd16(const uint8_t *p) { return p[0] | (p[1] << 8); }

class TagCallbacks : public NimBLEScanCallbacks {
  void onResult(const NimBLEAdvertisedDevice *dev) override {
    if (!dev->haveManufacturerData()) return;
    std::string md = dev->getManufacturerData();
    const uint8_t *p = (const uint8_t *)md.data();
    if (md.size() < 17 || rd16(p) != 0xFFFF || p[2] != 0xC7 || p[3] != 0x01) return;

    Reading r;
    r.tagId = p[4] | (p[5] << 8) | ((uint32_t)p[6] << 16) | ((uint32_t)p[7] << 24);
    r.seq = rd16(p + 8);
    if (isDuplicate(r.tagId, r.seq)) return;
    r.tempCenti = (int16_t)rd16(p + 10);
    r.rum = p[12];
    r.act = rd16(p + 13);
    r.battMv = p[15] * 20;
    r.flags = p[16];
    r.rssi = dev->getRSSI();
    r.ts = time(nullptr);

    portENTER_CRITICAL(&mux);
    if (batchLen < MAX_BATCH) batch[batchLen++] = r;
    portEXIT_CRITICAL(&mux);
  }
};

static void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) delay(250);
}

static bool upload() {
  Reading local[MAX_BATCH];
  size_t n;
  portENTER_CRITICAL(&mux);
  n = batchLen;
  memcpy(local, batch, n * sizeof(Reading));
  portEXIT_CRITICAL(&mux);
  if (n == 0) return true;

  connectWifi();
  if (WiFi.status() != WL_CONNECTED) return false;

  JsonDocument doc;
  doc["gateway_id"] = GATEWAY_ID;
  JsonArray arr = doc["readings"].to<JsonArray>();
  bool timeOk = time(nullptr) > 1700000000;
  for (size_t i = 0; i < n; i++) {
    JsonObject o = arr.add<JsonObject>();
    o["tag_id"] = local[i].tagId;
    o["seq"] = local[i].seq;
    if (local[i].tempCenti != 0x7FFF) o["temp_c"] = local[i].tempCenti / 100.0;
    o["rumination_min"] = local[i].rum;
    o["activity_mg"] = local[i].act;
    o["battery_mv"] = local[i].battMv;
    o["flags"] = local[i].flags;
    o["rssi"] = local[i].rssi;
    if (timeOk) {
      char buf[25];
      strftime(buf, sizeof buf, "%Y-%m-%dT%H:%M:%SZ", gmtime(&local[i].ts));
      o["ts"] = buf;
    }
  }
  String body;
  serializeJson(doc, body);

  WiFiClientSecure tls;
  tls.setInsecure();  // TODO for production: pin the server CA with tls.setCACert()
  HTTPClient http;
  bool https = String(API_URL).startsWith("https");
  WiFiClient plain;
  if (https) http.begin(tls, API_URL); else http.begin(plain, API_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Gateway-Key", GATEWAY_KEY);
  int code = http.POST(body);
  http.end();
  Serial.printf("[upload] %u readings -> HTTP %d\n", (unsigned)n, code);
  if (code < 200 || code >= 300) return false;

  // drop what we sent, keep anything that arrived meanwhile
  portENTER_CRITICAL(&mux);
  size_t extra = batchLen - n;
  memmove(batch, batch + n, extra * sizeof(Reading));
  batchLen = extra;
  portEXIT_CRITICAL(&mux);
  return true;
}

void setup() {
  Serial.begin(115200);
  connectWifi();
  configTime(0, 0, NTP_SERVER);

  NimBLEDevice::init("cattle-gw");
  NimBLEScan *scan = NimBLEDevice::getScan();
  scan->setScanCallbacks(new TagCallbacks(), true);
  scan->setActiveScan(false);       // adverts carry everything; passive saves power
  scan->setInterval(160);
  scan->setWindow(150);
  scan->setDuplicateFilter(false);
  scan->start(0, false, true);      // scan forever
  Serial.println("[gw] scanning for CattleHealth tags");
}

void loop() {
  static uint32_t last = 0;
  if (millis() - last >= UPLOAD_EVERY_MS) {
    last = millis();
    if (!upload()) Serial.println("[upload] failed, will retry");
  }
  if (!NimBLEDevice::getScan()->isScanning()) NimBLEDevice::getScan()->start(0, false, true);
  delay(50);
}
