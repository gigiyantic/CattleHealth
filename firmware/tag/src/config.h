#ifndef CH_CONFIG_H
#define CH_CONFIG_H
#define ACCEL_RATE_HZ          10      /* SC7A20 / LIS3DH low-power 10 Hz ODR */
#define FIFO_WATERMARK         25      /* wake every 2.5 s to drain FIFO */
#define REPORT_PERIOD_S        900     /* 15-minute report */
#define RUM_WINDOW_S           60      /* rumination classified per minute */
#define RUM_MIN_PEAKS          40      /* 0.67 Hz .. */
#define RUM_MAX_PEAKS          80      /* .. 1.33 Hz chewing rhythm */
#define RUM_PEAK_THRESH_MG     18      /* jaw motion amplitude threshold */
#define RUM_MAX_ACTIVITY_MG    120     /* reject walking / grazing bouts */
#define NTC_R_SERIES           10000.0
#define NTC_R0                 10000.0
#define NTC_T0_K               298.15
#define NTC_BETA               3950.0
#define LOW_BATT_MV            2500
#endif
