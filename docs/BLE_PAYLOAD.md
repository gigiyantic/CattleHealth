# BLE Advertisement Payload (v1)

Every 15 minutes each tag broadcasts one non-connectable BLE advertisement
(ADV_NONCONN_IND, 3 bursts on channels 37/38/39) carrying a
**Manufacturer Specific Data** AD structure.

| Offset | Size | Field | Encoding |
| ---: | ---: | --- | --- |
| 0 | 2 | Company ID | `0xFFFF` (little-endian, test ID until a Bluetooth SIG ID is assigned) |
| 2 | 1 | Magic | `0xC7` ("cattle") |
| 3 | 1 | Version | `0x01` |
| 4 | 4 | Tag ID | uint32 LE, burned at factory, printed on the pod |
| 8 | 2 | Sequence | uint16 LE, +1 per report, lets the cloud de-duplicate and spot gaps |
| 10 | 2 | Temperature | int16 LE, °C × 100 (e.g. `3870` = 38.70 °C). `0x7FFF` = sensor fault |
| 12 | 1 | Rumination | uint8, minutes spent chewing in the last 15-minute window (0–15) |
| 13 | 2 | Activity | uint16 LE, mean dynamic Signal Vector Magnitude (gravity removed per axis) in milli-g over the window |
| 15 | 1 | Battery | uint8, millivolts ÷ 20 (e.g. `150` = 3000 mV) |
| 16 | 1 | Flags | bit0 = low battery, bit1 = accel fault, bit2 = temp fault, bit3 = tamper (strap open) |

Total manufacturer data: **17 bytes** (fits comfortably in the 31-byte legacy advert
with the 3-byte Flags AD and 2-byte AD header).

## Gateway → Cloud JSON

The ESP32 gateway decodes the advert and batches readings:

```json
POST /api/v1/ingest
X-Gateway-Key: <farm gateway key>

{
  "gateway_id": "gw-farm-0001",
  "readings": [
    {
      "tag_id": 1001,
      "seq": 512,
      "ts": "2026-11-04T10:15:00Z",
      "temp_c": 38.7,
      "rumination_min": 9,
      "activity_mg": 64,
      "battery_mv": 3000,
      "flags": 0,
      "rssi": -71
    }
  ]
}
```

`ts` is optional — the cloud stamps the receive time if the gateway has no NTP sync.
