/* On-tag motion processing: rumination minutes + activity (SVM) per report. */
#ifndef CH_MOTION_H
#define CH_MOTION_H
#include <stdint.h>
#include <stddef.h>
#include "hal.h"

typedef struct {
    /* per-minute window */
    uint16_t n;                 /* samples in current minute */
    int32_t  ema_q8[3];         /* per-axis gravity estimate (Q8) */
    int      primed;
    int16_t  prev, prev2;       /* last filtered values for peak detection */
    uint16_t peaks;
    uint32_t svm_dev_sum;       /* sum of dynamic SVM, milli-g */
    int      armed;             /* hysteresis: must go below -thresh before next peak */
    /* per-report accumulators */
    uint8_t  rum_minutes;
    uint32_t act_sum;
    uint32_t act_n;
} motion_t;

void     motion_init(motion_t *m);
void     motion_feed(motion_t *m, const accel_sample_t *s, size_t n);
uint8_t  motion_take_rumination(motion_t *m);   /* resets */
uint16_t motion_take_activity(motion_t *m);     /* resets */
uint16_t isqrt32(uint32_t v);
#endif
