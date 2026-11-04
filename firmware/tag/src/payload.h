#ifndef CH_PAYLOAD_H
#define CH_PAYLOAD_H
#include <stdint.h>
#include <stddef.h>
#define PAYLOAD_LEN       17
#define PAYLOAD_COMPANY   0xFFFF
#define PAYLOAD_MAGIC     0xC7
#define PAYLOAD_VERSION   0x01
#define FLAG_LOW_BATT     0x01
#define FLAG_ACCEL_FAULT  0x02
#define FLAG_TEMP_FAULT   0x04
#define FLAG_TAMPER       0x08

typedef struct {
    uint32_t tag_id;
    uint16_t seq;
    int16_t  temp_centi_c;
    uint8_t  rumination_min;
    uint16_t activity_mg;
    uint16_t battery_mv;
    uint8_t  flags;
} report_t;

size_t payload_encode(const report_t *r, uint8_t out[PAYLOAD_LEN]);
int    payload_decode(const uint8_t *in, size_t len, report_t *r);
#endif
