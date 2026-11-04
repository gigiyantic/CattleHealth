#include "motion.h"
#include "config.h"

#define SAMPLES_PER_MIN (ACCEL_RATE_HZ * RUM_WINDOW_S)

uint16_t isqrt32(uint32_t v)
{
    uint32_t r = 0, bit = 1UL << 30;
    while (bit > v) bit >>= 2;
    while (bit) {
        if (v >= r + bit) { v -= r + bit; r = (r >> 1) + bit; }
        else r >>= 1;
        bit >>= 2;
    }
    return (uint16_t)r;
}

void motion_init(motion_t *m)
{
    *m = (motion_t){0};
}

static void close_minute(motion_t *m)
{
    uint32_t act = m->n ? m->svm_dev_sum / m->n : 0;
    if (m->peaks >= RUM_MIN_PEAKS && m->peaks <= RUM_MAX_PEAKS && act <= RUM_MAX_ACTIVITY_MG) {
        if (m->rum_minutes < 255) m->rum_minutes++;
    }
    m->act_sum += act;
    m->act_n++;
    m->n = 0; m->peaks = 0; m->svm_dev_sum = 0;
}

void motion_feed(motion_t *m, const accel_sample_t *s, size_t n)
{
    for (size_t i = 0; i < n; i++) {
        int32_t v[3] = { s[i].x, s[i].y, s[i].z };
        int32_t d[3];
        /* remove gravity/posture per axis with a slow EMA (alpha = 1/16, ~1.6 s) */
        for (int k = 0; k < 3; k++) {
            int32_t q = v[k] * 256;
            if (!m->primed) m->ema_q8[k] = q;
            m->ema_q8[k] += (q - m->ema_q8[k]) / 16;
            d[k] = (q - m->ema_q8[k]) / 256;
        }
        m->primed = 1;
        /* activity: SVM of the dynamic acceleration (milli-g) */
        m->svm_dev_sum += isqrt32((uint32_t)(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]));
        /* jaw axis = Y on a neck collar */
        int16_t f = (int16_t)d[1];

        /* peak = local max above threshold, re-armed after dipping below -thresh/2 */
        if (f < -RUM_PEAK_THRESH_MG / 2) m->armed = 1;
        if (m->armed && m->prev > RUM_PEAK_THRESH_MG && m->prev >= m->prev2 && m->prev > f) {
            m->peaks++;
            m->armed = 0;
        }
        m->prev2 = m->prev;
        m->prev = f;

        if (++m->n >= SAMPLES_PER_MIN) close_minute(m);
    }
}

uint8_t motion_take_rumination(motion_t *m)
{
    uint8_t r = m->rum_minutes;
    m->rum_minutes = 0;
    return r;
}

uint16_t motion_take_activity(motion_t *m)
{
    uint16_t a = m->act_n ? (uint16_t)(m->act_sum / m->act_n) : 0;
    m->act_sum = 0; m->act_n = 0;
    return a;
}
