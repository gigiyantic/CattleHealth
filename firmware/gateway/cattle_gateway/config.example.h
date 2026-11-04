// Copy to config.h and fill in. config.h is git-ignored.
#pragma once
#define WIFI_SSID        "farm-wifi"
#define WIFI_PASS        "change-me"
#define API_URL          "https://your-server.example.com/api/v1/ingest"
#define GATEWAY_ID       "gw-farm-0001"
#define GATEWAY_KEY      "dev-gateway-key"
#define UPLOAD_EVERY_MS  60000UL    // flush batch every minute
#define MAX_BATCH        120        // ~50 cows x 2 reports of buffer
#define NTP_SERVER       "pool.ntp.org"
