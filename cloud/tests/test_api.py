from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from cattlehealth.api import create_app
from cattlehealth.messages import MESSAGES, render
from cattlehealth.simulate import generate

GW = {"X-Gateway-Key": "dev-gateway-key"}


def client():
    return TestClient(create_app(":memory:"))


def ingest(c, rows, gw="gw-test"):
    out = {"accepted": 0, "duplicates": 0, "alerts": []}
    for i in range(0, len(rows), 1000):
        r = c.post("/api/v1/ingest", headers=GW, json={"gateway_id": gw, "readings": rows[i:i + 1000]})
        assert r.status_code == 200, r.text
        j = r.json()
        out["accepted"] += j["accepted"]; out["duplicates"] += j["duplicates"]; out["alerts"] += j["alerts"]
    return out


def test_rejects_bad_gateway_key():
    c = client()
    r = c.post("/api/v1/ingest", headers={"X-Gateway-Key": "nope"}, json={"gateway_id": "x", "readings": []})
    assert r.status_code == 401


def test_full_flow_with_alerts_and_dedup():
    c = client()
    farm = c.post("/api/v1/farms", json={"name": "Test farm", "owner_phone": "919800000000", "language": "hi"}).json()
    c.post(f"/api/v1/gateways/gw-test/farm/{farm['id']}")
    c.post("/api/v1/cows", json={"tag_id": 1003, "farm_id": farm["id"], "name": "Kamdhenu"})

    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    rows = list(generate(6, 8, end))
    res = ingest(c, rows)
    assert res["accepted"] == len(rows)
    kinds = {(a["tag_id"], a["kind"]) for a in res["alerts"]}
    assert (1003, "fever") in kinds
    assert (1005, "heat") in kinds
    fever = next(a for a in res["alerts"] if a["kind"] == "fever")
    assert "Kamdhenu" in fever["message"] and "बुखार" in fever["message"]   # Hindi farm

    # resending is de-duplicated and does not re-alert (cooldown)
    again = ingest(c, rows[-200:])
    assert again["accepted"] == 0 and again["duplicates"] == 200 and again["alerts"] == []

    cows = c.get("/api/v1/cows", params={"farm_id": farm["id"]}).json()
    assert len(cows) == 6
    st = {x["tag_id"]: x["status"] for x in cows}
    assert st[1003] in ("warning", "critical") and st[1005] == "heat" and st[1001] == "ok"

    d = c.get("/api/v1/cows/1003", params={"hours": 24}).json()
    assert d["name"] == "Kamdhenu" and len(d["series"]) >= 90 and len(d["daily_rumination"]) == 7

    active = c.get("/api/v1/alerts", params={"active": True}).json()
    aid = active[0]["id"]
    assert c.post(f"/api/v1/alerts/{aid}/ack").json()["acknowledged"]
    assert len(c.get("/api/v1/alerts", params={"active": True}).json()) == len(active) - 1


def test_offline_sweep():
    c = client()
    old = datetime.now(timezone.utc) - timedelta(hours=5)
    ingest(c, [{"tag_id": 2001, "ts": old.strftime("%Y-%m-%dT%H:%M:%SZ"), "temp_c": 38.5,
                "rumination_min": 5, "activity_mg": 30, "battery_mv": 3000}])
    res = c.post("/api/v1/sweep").json()
    assert [a["kind"] for a in res["alerts"]] == ["offline"]


def test_whatsapp_webhook_verify():
    c = client()
    r = c.get("/webhook/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "cattlehealth-verify",
                                           "hub.challenge": "42"})
    assert r.text == "42"
    assert c.get("/webhook/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "bad"}).status_code == 403


def test_all_languages_have_all_messages():
    keys = set(MESSAGES["en"])
    for lang, table in MESSAGES.items():
        assert set(table) == keys, lang
    assert "Gauri" in render("heat", "ta", cow="Gauri", ratio="3.4")
