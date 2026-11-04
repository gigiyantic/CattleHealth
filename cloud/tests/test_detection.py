from datetime import datetime, timedelta, timezone

from cattlehealth.detection import (daily_rumination, detect_heat, detect_rumination, detect_temperature,
                                    detect_device, evaluate, status_from, temp_baseline)
from cattlehealth.simulate import generate

NOW = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)


def series(days=4, temp=38.6, rum=5, act=30, mutate=None):
    out = []
    n = int(days * 96)
    for i in range(n + 1):
        ts = NOW - timedelta(minutes=15 * (n - i))
        r = {"ts": ts, "temp_c": temp, "rumination_min": rum, "activity_mg": act, "battery_mv": 3000, "flags": 0}
        if mutate:
            mutate(r, (NOW - ts).total_seconds() / 3600)
        out.append(r)
    return out


def test_healthy_cow_has_no_findings():
    rs = series()
    assert evaluate(rs, NOW) == []
    assert status_from([]) == "ok"
    assert temp_baseline(rs, NOW) == 38.6
    assert round(daily_rumination(rs, NOW)) == 480


def test_fever_needs_two_consecutive_high_readings():
    def one_spike(r, h):
        if h == 0:
            r["temp_c"] = 39.9
    assert detect_temperature(series(mutate=one_spike), NOW) == []

    def fever(r, h):
        if h <= 0.5:
            r["temp_c"] = 39.8
    f = detect_temperature(series(mutate=fever), NOW)
    assert f and f[0].kind == "fever" and f[0].severity == "warning"


def test_relative_fever_uses_cow_baseline():
    def fever(r, h):
        if h <= 0.5:
            r["temp_c"] = 39.4        # below absolute threshold, but +1.2 over this cow's 38.2 baseline
    f = detect_temperature(series(temp=38.2, mutate=fever), NOW)
    assert f and f[0].kind == "fever"
    assert f[0].params["base"] == "38.2"


def test_critical_fever_and_hypothermia():
    def hot(r, h):
        if h <= 0.5:
            r["temp_c"] = 40.7
    assert detect_temperature(series(mutate=hot), NOW)[0].severity == "critical"

    def cold(r, h):
        if h <= 0.5:
            r["temp_c"] = 37.1
    assert detect_temperature(series(mutate=cold), NOW)[0].kind == "hypothermia"


def test_low_rumination():
    def drop(r, h):
        if h <= 24:
            r["rumination_min"] = 2      # 2 * 96 = 192 min/day
    f = detect_rumination(series(days=8, mutate=drop), NOW)
    assert f and f[0].kind == "rumination" and f[0].severity == "critical"


def test_relative_rumination_drop():
    def drop(r, h):
        if h <= 24:
            r["rumination_min"] = 3      # 288/day vs usual 480 -> warning
    f = detect_rumination(series(days=8, mutate=drop), NOW)
    assert f and f[0].severity == "warning"


def test_rumination_needs_coverage():
    rs = series(days=2)[::3]   # only a third of reports arrived
    assert detect_rumination(rs, NOW) == []


def test_heat_detection():
    def heat(r, h):
        if h <= 3:
            r["activity_mg"] = 120
    f = detect_heat(series(days=8, mutate=heat), NOW)
    assert f and f[0].kind == "heat" and float(f[0].params["ratio"]) >= 3
    assert status_from(f) == "heat"


def test_heat_needs_history():
    def heat(r, h):
        if h <= 3:
            r["activity_mg"] = 120
    assert detect_heat(series(days=0.5, mutate=heat), NOW) == []


def test_device_findings():
    rs = series(days=1)
    rs[-1]["flags"] = 1 | 8
    kinds = {f.kind for f in detect_device(rs, NOW)}
    assert kinds == {"low_battery", "tamper"}
    assert [f.kind for f in detect_device(rs, NOW + timedelta(hours=3))] .count("offline") == 1


def test_simulator_scenarios_are_detected():
    from datetime import datetime as dt
    end = NOW
    rows = list(generate(10, 8, end))
    by_tag = {}
    for r in rows:
        r = dict(r, ts=dt.fromisoformat(r["ts"].replace("Z", "+00:00")))
        by_tag.setdefault(r["tag_id"], []).append(r)
    kinds = {tag: {f.kind for f in evaluate(rs, end)} for tag, rs in by_tag.items()}
    assert "fever" in kinds[1003]
    assert "heat" in kinds[1005]
    assert "rumination" in kinds[1007]
    assert "low_battery" in kinds[1009]
    healthy = [t for t in kinds if t not in (1003, 1005, 1007, 1009)]
    assert all(not kinds[t] for t in healthy), {t: kinds[t] for t in healthy}
