#include "ntc.h"
#include "config.h"
#include <math.h>

int16_t ntc_adc_to_centi_c(uint16_t adc)
{
    if (adc <= 10 || adc >= 4085) return INT16_MAX;          /* short / open */
    double r = NTC_R_SERIES * (double)adc / (4095.0 - (double)adc);
    double inv_t = 1.0 / NTC_T0_K + log(r / NTC_R0) / NTC_BETA;
    double c = 1.0 / inv_t - 273.15;
    return (int16_t)lround(c * 100.0);
}
