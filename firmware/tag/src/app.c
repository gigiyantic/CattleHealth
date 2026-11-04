/* Tag main loop: ~4 uA average.
 *  - accelerometer runs autonomously at 10 Hz into its FIFO
 *  - MCU wakes on FIFO watermark (every 2.5 s, ~1 ms of work) to update motion stats
 *  - every 15 minutes: read NTC + battery, encode payload, advertise, sleep */
#include "app.h"
#include "hal.h"
#include "config.h"
#include "motion.h"
#include "ntc.h"
#include "payload.h"

static motion_t g_motion;
static uint16_t g_seq;
static uint32_t g_next_report;

void app_init(void)
{
    hal_init();
    motion_init(&g_motion);
    g_seq = 0;
    g_next_report = hal_uptime_s() + REPORT_PERIOD_S;
}

void app_build_report(report_t *r)
{
    r->tag_id = hal_tag_id();
    r->seq = g_seq++;
    r->temp_centi_c = ntc_adc_to_centi_c(hal_ntc_adc_read());
    r->rumination_min = motion_take_rumination(&g_motion);
    r->activity_mg = motion_take_activity(&g_motion);
    r->battery_mv = hal_battery_mv();
    r->flags = 0;
    if (r->battery_mv < LOW_BATT_MV) r->flags |= FLAG_LOW_BATT;
    if (!hal_accel_ok()) r->flags |= FLAG_ACCEL_FAULT;
    if (r->temp_centi_c == INT16_MAX) r->flags |= FLAG_TEMP_FAULT;
    if (hal_tamper_open()) r->flags |= FLAG_TAMPER;
}

void app_step(void)
{
    accel_sample_t buf[32];
    size_t n;
    while ((n = hal_accel_read_fifo(buf, 32)) > 0) motion_feed(&g_motion, buf, n);

    if ((int32_t)(hal_uptime_s() - g_next_report) >= 0) {
        report_t r;
        uint8_t adv[PAYLOAD_LEN];
        app_build_report(&r);
        payload_encode(&r, adv);
        hal_ble_advertise(adv, sizeof adv);
        g_next_report += REPORT_PERIOD_S;
    }
    hal_sleep_until_event();
}

#ifndef CH_HOST_TEST
int main(void)
{
    app_init();
    for (;;) app_step();
}
#endif
