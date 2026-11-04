#ifndef CH_NTC_H
#define CH_NTC_H
#include <stdint.h>
/* NTC on the low side of a divider: Vadc = Vref * Rntc / (Rseries + Rntc).
 * Returns °C x 100, or INT16_MAX on open/short circuit. */
int16_t ntc_adc_to_centi_c(uint16_t adc12);
#endif
