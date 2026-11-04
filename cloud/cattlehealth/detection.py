"""Veterinary detection algorithms (pure functions, no I/O).

Input: readings for one cow, each a dict with keys
    ts (datetime, UTC), temp_c, rumination_min, activity_mg, battery_mv, flags
sorted oldest -> newest. Tags report every 15 minutes (96 per day).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median
from typing import Iterable, List, Optional

REPORT_MIN = 15
PER_DAY = 24 * 60 // REPORT_MIN  # 96

DEFAULT_BASELINE_C = 38.6
FEVER_DELTA_C = 1.0
FEVER_ABS_C = 39.8          # absolute fever even without a baseline
CRITICAL_FEVER_C = 40.5
HYPOTHERMIA_C = 37.5         # milk fever / shock
RUMINATION_LOW_MIN = 300
RUMINATION_CRITICAL_MIN = 200
RUMINATION_DROP_RATIO = 0.7
HEAT_RATIO = 3.0
HEAT_WINDOW_H = 3
LOW_BATTERY_MV = 2500
OFFLINE_AFTER_H = 2

FLAG_LOW_BATT, FLAG_ACCEL_FAULT, FLAG_TEMP_FAULT, FLAG_TAMPER = 1, 2, 4, 8


@dataclass
class Finding:
    kind: str
    severity: str          # info | warning | critical
    value: float
    params: dict


def _window(readings, start: datetime, end: datetime):
    return [r for r in readings if start <= r["ts"] <= end]


def temp_baseline(readings, now: datetime) -> Optional[float]:
    """Median temperature over the previous 3 days (excluding the last 6 h and fever-range values)."""
    temps = [r["temp_c"] for r in _window(readings, now - timedelta(hours=72), now - timedelta(hours=6))
             if r.get("temp_c") is not None and 36.5 <= r["temp_c"] < 39.5]
    return round(median(temps), 2) if len(temps) >= 24 else None


def detect_temperature(readings, now: datetime) -> List[Finding]:
    recent = [r for r in readings if r.get("temp_c") is not None and r["ts"] > now - timedelta(minutes=50)][-2:]
    if len(recent) < 2:
        return []
    base = temp_baseline(readings, now)
    ref = base if base is not None else DEFAULT_BASELINE_C
    t_now = recent[-1]["temp_c"]
    lows = min(r["temp_c"] for r in recent)
    highs = max(r["temp_c"] for r in recent)

    # both of the last two consecutive readings must cross the threshold
    if lows >= ref + FEVER_DELTA_C or lows >= FEVER_ABS_C:
        sev = "critical" if (t_now >= CRITICAL_FEVER_C or lows >= ref + 1.5) else "warning"
        return [Finding("fever", sev, t_now, {"temp": f"{t_now:.1f}", "base": f"{ref:.1f}"})]
    if highs <= HYPOTHERMIA_C:
        return [Finding("hypothermia", "critical", t_now, {"temp": f"{t_now:.1f}"})]
    return []


def daily_rumination(readings, end: datetime) -> Optional[float]:
    """Rumination minutes in the 24 h before `end`, scaled for missing reports. None if <80% coverage."""
    day = [r for r in _window(readings, end - timedelta(hours=24), end) if r.get("rumination_min") is not None]
    if len(day) < 0.8 * PER_DAY:
        return None
    return sum(r["rumination_min"] for r in day) * PER_DAY / len(day)


def detect_rumination(readings, now: datetime) -> List[Finding]:
    today = daily_rumination(readings, now)
    if today is None:
        return []
    prior = [d for d in (daily_rumination(readings, now - timedelta(days=i)) for i in range(1, 8)) if d is not None]
    usual = median(prior) if len(prior) >= 3 else None
    low_abs = today < RUMINATION_LOW_MIN
    low_rel = usual is not None and today < usual * RUMINATION_DROP_RATIO
    if not (low_abs or low_rel):
        return []
    sev = "critical" if today < RUMINATION_CRITICAL_MIN else "warning"
    return [Finding("rumination", sev, round(today), {"mins": str(round(today)),
                                                       "usual": str(round(usual)) if usual else "450–550"})]


def detect_heat(readings, now: datetime) -> List[Finding]:
    recent = [r["activity_mg"] for r in _window(readings, now - timedelta(hours=HEAT_WINDOW_H), now)
              if r.get("activity_mg") is not None]
    if len(recent) < HEAT_WINDOW_H * 4 * 0.75:
        return []
    base_vals = [r["activity_mg"] for r in _window(readings, now - timedelta(days=7), now - timedelta(hours=12))
                 if r.get("activity_mg") is not None]
    if len(base_vals) < PER_DAY:      # need at least one day of history
        return []
    base = max(median(base_vals), 5.0)
    avg = sum(recent) / len(recent)
    ratio = avg / base
    if ratio >= HEAT_RATIO:
        return [Finding("heat", "info", round(ratio, 1), {"ratio": f"{ratio:.1f}"})]
    return []


def detect_device(readings, now: datetime) -> List[Finding]:
    if not readings:
        return []
    last = readings[-1]
    out = []
    mv = last.get("battery_mv") or 0
    if (last.get("flags", 0) & FLAG_LOW_BATT) or (0 < mv < LOW_BATTERY_MV):
        out.append(Finding("low_battery", "info", mv, {"mv": str(mv)}))
    if last.get("flags", 0) & FLAG_TAMPER:
        out.append(Finding("tamper", "warning", 1, {}))
    hours = (now - last["ts"]).total_seconds() / 3600
    if hours >= OFFLINE_AFTER_H:
        out.append(Finding("offline", "warning", round(hours, 1), {"hours": str(int(hours))}))
    return out


def evaluate(readings: Iterable[dict], now: datetime) -> List[Finding]:
    rs = sorted(readings, key=lambda r: r["ts"])
    return (detect_temperature(rs, now) + detect_rumination(rs, now) +
            detect_heat(rs, now) + detect_device(rs, now))


def status_from(findings: List[Finding]) -> str:
    sev = {f.severity for f in findings if f.kind not in ("low_battery",)}
    if "critical" in sev:
        return "critical"
    if "warning" in sev:
        return "warning"
    if any(f.kind == "heat" for f in findings):
        return "heat"
    return "ok"
