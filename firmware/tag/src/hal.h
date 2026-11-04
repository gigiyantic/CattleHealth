/* Hardware abstraction layer — implement once per SoC (PHY6222 / TLSR8251).
 * Everything above this file is portable C99 and unit-tested on the host. */
#ifndef CH_HAL_H
#define CH_HAL_H
#include <stdint.h>
#include <stddef.h>

typedef struct { int16_t x, y, z; } accel_sample_t;   /* milli-g */

void     hal_init(void);
uint32_t hal_tag_id(void);                  /* factory ID from flash/eFuse */
uint16_t hal_ntc_adc_read(void);            /* 12-bit ADC of NTC divider, 0..4095 */
uint16_t hal_battery_mv(void);
int      hal_tamper_open(void);             /* 1 if strap reed switch is open */
/* Drain accelerometer FIFO; returns number of samples written (<= max). */
size_t   hal_accel_read_fifo(accel_sample_t *buf, size_t max);
int      hal_accel_ok(void);
/* Send one non-connectable advert burst with manufacturer data. */
void     hal_ble_advertise(const uint8_t *mfg_data, size_t len);
/* Sleep until accelerometer FIFO watermark IRQ or RTC alarm. */
void     hal_sleep_until_event(void);
uint32_t hal_uptime_s(void);                /* 32.768 kHz RTC based */
#endif
