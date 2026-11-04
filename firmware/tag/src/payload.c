#include "payload.h"

static void put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }

size_t payload_encode(const report_t *r, uint8_t o[PAYLOAD_LEN])
{
    put16(o + 0, PAYLOAD_COMPANY);
    o[2] = PAYLOAD_MAGIC;
    o[3] = PAYLOAD_VERSION;
    o[4] = (uint8_t)r->tag_id; o[5] = (uint8_t)(r->tag_id >> 8);
    o[6] = (uint8_t)(r->tag_id >> 16); o[7] = (uint8_t)(r->tag_id >> 24);
    put16(o + 8, r->seq);
    put16(o + 10, (uint16_t)r->temp_centi_c);
    o[12] = r->rumination_min;
    put16(o + 13, r->activity_mg);
    uint16_t b = (uint16_t)((r->battery_mv + 10) / 20);
    o[15] = (uint8_t)(b > 255 ? 255 : b);
    o[16] = r->flags;
    return PAYLOAD_LEN;
}

int payload_decode(const uint8_t *p, size_t len, report_t *r)
{
    if (len < PAYLOAD_LEN || get16(p) != PAYLOAD_COMPANY || p[2] != PAYLOAD_MAGIC || p[3] != PAYLOAD_VERSION)
        return -1;
    r->tag_id = (uint32_t)p[4] | ((uint32_t)p[5] << 8) | ((uint32_t)p[6] << 16) | ((uint32_t)p[7] << 24);
    r->seq = get16(p + 8);
    r->temp_centi_c = (int16_t)get16(p + 10);
    r->rumination_min = p[12];
    r->activity_mg = get16(p + 13);
    r->battery_mv = (uint16_t)(p[15] * 20);
    r->flags = p[16];
    return 0;
}
