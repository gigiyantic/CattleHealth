#ifndef SIM_H
#define SIM_H
#include <stdint.h>
#include <stddef.h>
enum { MODE_REST, MODE_RUMINATE, MODE_WALK };
typedef struct {
    uint32_t t_ms; int mode; size_t pending;
    uint16_t ntc_adc, batt_mv;
    uint8_t last_adv[32]; size_t adv_len; int adv_count;
} sim_t;
extern sim_t SIM;
#endif
