/* Host simulation of the HAL: synthetic cow motion + fixed sensors. */
#include "../src/hal.h"
#include "../src/config.h"
#include "sim.h"
#include <math.h>
#include <string.h>

sim_t SIM;
static uint32_t rng = 12345;
static int noise(int amp) { rng = rng * 1103515245u + 12345u; return (int)((rng >> 16) % (2 * amp + 1)) - amp; }

void hal_init(void) {}
uint32_t hal_tag_id(void) { return 1001; }
uint16_t hal_ntc_adc_read(void) { return SIM.ntc_adc; }
uint16_t hal_battery_mv(void) { return SIM.batt_mv; }
int hal_tamper_open(void) { return 0; }
int hal_accel_ok(void) { return 1; }
uint32_t hal_uptime_s(void) { return SIM.t_ms / 1000; }
void hal_sleep_until_event(void) {}

size_t hal_accel_read_fifo(accel_sample_t *b, size_t max)
{
    if (SIM.pending == 0) return 0;
    size_t n = SIM.pending < max ? SIM.pending : max;
    for (size_t i = 0; i < n; i++) {
        double t = SIM.t_ms / 1000.0;
        double y = 0, x = 0;
        if (SIM.mode == MODE_RUMINATE) y = 60 * sin(2 * M_PI * 1.0 * t);
        if (SIM.mode == MODE_WALK) { x = 450 * sin(2 * M_PI * 1.8 * t); y = 300 * sin(2 * M_PI * 0.9 * t + 1); }
        b[i].x = (int16_t)(x + noise(4));
        b[i].y = (int16_t)(y + noise(4));
        b[i].z = (int16_t)(1000 + noise(4));
        SIM.t_ms += 1000 / ACCEL_RATE_HZ;
    }
    SIM.pending -= n;
    return n;
}

void hal_ble_advertise(const uint8_t *d, size_t len)
{
    memcpy(SIM.last_adv, d, len);
    SIM.adv_len = len;
    SIM.adv_count++;
}
