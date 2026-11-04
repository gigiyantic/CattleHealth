#include <stdio.h>
#include <stdlib.h>
#include "../src/app.h"
#include "../src/config.h"
#include "../src/motion.h"
#include "../src/ntc.h"
#include "../src/payload.h"
#include "sim.h"

static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; printf("FAIL %s:%d ", __FILE__, __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

/* run the app for `minutes` in a given motion mode */
static void run(int mode, int minutes)
{
    SIM.mode = mode;
    for (int i = 0; i < minutes * 60 * ACCEL_RATE_HZ / FIFO_WATERMARK; i++) {
        SIM.pending = FIFO_WATERMARK;
        app_step();
    }
}

static uint16_t adc_for_c(double c)
{
    for (uint16_t a = 11; a < 4085; a++) if (ntc_adc_to_centi_c(a) <= (int)(c * 100)) return a;
    return 0;
}

int main(void)
{
    /* NTC: 25 C at midpoint, monotonic, fault detection */
    CHECK(abs(ntc_adc_to_centi_c(2048) - 2500) < 5, "ntc 25C got %d", ntc_adc_to_centi_c(2048));
    CHECK(ntc_adc_to_centi_c(1000) > ntc_adc_to_centi_c(2000), "ntc monotonic");
    CHECK(ntc_adc_to_centi_c(0) == INT16_MAX && ntc_adc_to_centi_c(4095) == INT16_MAX, "ntc fault");

    /* payload round trip */
    report_t r = { 0xA1B2C3D4, 513, 3870, 9, 64, 3000, FLAG_LOW_BATT }, d;
    uint8_t buf[PAYLOAD_LEN];
    CHECK(payload_encode(&r, buf) == 17, "len");
    CHECK(payload_decode(buf, 17, &d) == 0, "decode");
    CHECK(d.tag_id == r.tag_id && d.seq == 513 && d.temp_centi_c == 3870 && d.rumination_min == 9 &&
          d.activity_mg == 64 && d.battery_mv == 3000 && d.flags == FLAG_LOW_BATT, "round trip");
    buf[2] = 0; CHECK(payload_decode(buf, 17, &d) != 0, "bad magic rejected");

    CHECK(isqrt32(1000000) == 1000 && isqrt32(2) == 1, "isqrt");

    /* full app: 15 min = 10 ruminating + 5 resting -> ~10 rumination minutes, low activity */
    SIM.ntc_adc = adc_for_c(38.6); SIM.batt_mv = 3010;
    app_init();
    run(MODE_RUMINATE, 10);
    run(MODE_REST, 5);
    CHECK(SIM.adv_count == 1, "one advert per 15 min, got %d", SIM.adv_count);
    payload_decode(SIM.last_adv, SIM.adv_len, &d);
    printf("window1: temp=%.2f rum=%u act=%u batt=%u flags=%u\n", d.temp_centi_c / 100.0, d.rumination_min, d.activity_mg, d.battery_mv, d.flags);
    CHECK(d.rumination_min >= 9 && d.rumination_min <= 10, "rumination minutes %u", d.rumination_min);
    CHECK(d.activity_mg < 60, "rest activity %u", d.activity_mg);
    CHECK(abs(d.temp_centi_c - 3860) <= 5, "temp %d", d.temp_centi_c);

    /* walking 15 min: no rumination, high activity */
    run(MODE_WALK, 15);
    CHECK(SIM.adv_count == 2, "second advert");
    payload_decode(SIM.last_adv, SIM.adv_len, &d);
    printf("window2: rum=%u act=%u seq=%u\n", d.rumination_min, d.activity_mg, d.seq);
    CHECK(d.rumination_min == 0, "walking is not rumination (%u)", d.rumination_min);
    CHECK(d.activity_mg > 150, "walking activity %u", d.activity_mg);
    CHECK(d.seq == 1, "seq increments");

    /* low battery flag */
    SIM.batt_mv = 2400; run(MODE_REST, 15);
    payload_decode(SIM.last_adv, SIM.adv_len, &d);
    CHECK(d.flags & FLAG_LOW_BATT, "low batt flag");

    printf(fails ? "%d FAILED\n" : "all tag firmware tests passed\n", fails);
    return fails ? 1 : 0;
}
