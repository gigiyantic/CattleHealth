"""Herd simulator: generates realistic tag data (with injected health events) and posts it
through the real gateway ingest API.

    python -m cattlehealth.simulate --url http://localhost:8000 --cows 12 --days 8
"""
from __future__ import annotations

import argparse
import math
import random
from datetime import datetime, timedelta, timezone

import httpx

NAMES = ["Gauri", "Lakshmi", "Kamdhenu", "Nandini", "Radha", "Ganga", "Sundari", "Kapila",
         "Shyama", "Bhuri", "Chandni", "Moti", "Heera", "Rani", "Tulsi", "Sona"]

# cow index -> scenario
SCENARIOS = {2: "fever", 4: "heat", 6: "rumination", 8: "low_battery"}


def generate(n_cows: int, days: int, end: datetime, seed: int = 7):
    rnd = random.Random(seed)
    start = end - timedelta(days=days)
    steps = int(days * 96)
    for i in range(n_cows):
        tag = 1001 + i
        scen = SCENARIOS.get(i)
        base_t = rnd.uniform(38.4, 38.8)
        rum_scale = rnd.uniform(0.95, 1.1)
        act_scale = rnd.uniform(0.8, 1.2)
        batt = rnd.randint(2950, 3050) if scen != "low_battery" else 2440
        for s in range(steps + 1):
            ts = start + timedelta(minutes=15 * s)
            hrs_to_end = (end - ts).total_seconds() / 3600
            h = ts.hour + ts.minute / 60 + 5.5  # IST local time for the daily rhythm
            temp = base_t + 0.3 * math.sin(2 * math.pi * (h - 10) / 24) + rnd.gauss(0, 0.07)
            night = 1.25 if (h % 24) < 6 or (h % 24) > 21 else 0.85
            rum = rnd.gauss(5.2 * night * rum_scale, 1.6)
            act = rnd.gauss((18 if night > 1 else 38) * act_scale, 6)
            if scen == "fever" and hrs_to_end <= 6:
                temp += 1.6
                rum *= 0.6
            if scen == "rumination" and hrs_to_end <= 30:
                rum *= 0.35
            if scen == "heat" and hrs_to_end <= 4:
                act *= 4.2
                rum *= 0.7
            yield {
                "tag_id": tag, "seq": s % 65536, "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "temp_c": round(temp, 2), "rumination_min": int(max(0, min(15, round(rum)))),
                "activity_mg": int(max(0, round(act))), "battery_mv": batt,
                "flags": 1 if batt < 2500 else 0, "rssi": rnd.randint(-85, -55),
            }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--gateway-key", default="dev-gateway-key")
    ap.add_argument("--api-key", default="")
    ap.add_argument("--gateway-id", default="gw-demo-farm")
    ap.add_argument("--cows", type=int, default=12)
    ap.add_argument("--days", type=float, default=8)
    ap.add_argument("--phone", default="", help="farmer WhatsApp number, e.g. 919876543210")
    ap.add_argument("--lang", default="hi")
    a = ap.parse_args()

    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    end -= timedelta(minutes=end.minute % 15)
    hdr = {"X-API-Key": a.api_key} if a.api_key else {}
    with httpx.Client(base_url=a.url, timeout=60) as c:
        farm = c.post("/api/v1/farms", headers=hdr, json={"name": "Demo Dairy, Anand", "owner_phone": a.phone or None,
                                                          "language": a.lang}).json()
        c.post(f"/api/v1/gateways/{a.gateway_id}/farm/{farm['id']}", headers=hdr)
        for i in range(a.cows):
            c.post("/api/v1/cows", headers=hdr, json={"tag_id": 1001 + i, "farm_id": farm["id"],
                                                      "name": NAMES[i % len(NAMES)], "breed": "Gir" if i % 2 else "HF cross"})
        batch, total, alerts = [], 0, 0
        for r in generate(a.cows, a.days, end):
            batch.append(r)
            if len(batch) == 1000:
                res = c.post("/api/v1/ingest", headers={"X-Gateway-Key": a.gateway_key},
                             json={"gateway_id": a.gateway_id, "readings": batch}).json()
                total += res["accepted"]; alerts += len(res["alerts"]); batch = []
        if batch:
            res = c.post("/api/v1/ingest", headers={"X-Gateway-Key": a.gateway_key},
                         json={"gateway_id": a.gateway_id, "readings": batch}).json()
            total += res["accepted"]; alerts += len(res["alerts"])
    print(f"farm {farm['id']}: {a.cows} cows, {total} readings ingested, {alerts} alerts raised")


if __name__ == "__main__":
    main()
