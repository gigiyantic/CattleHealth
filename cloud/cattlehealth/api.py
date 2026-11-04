"""CattleHealth AI cloud API + dashboard host.

Run:  uvicorn cattlehealth.api:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .alerts import iso, raise_alerts, send_whatsapp
from .config import settings
from .db import DB
from .detection import daily_rumination, evaluate, status_from, temp_baseline
from .messages import LANGS, render

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("cattlehealth")

HISTORY_DAYS = 8


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


# ---------------------------------------------------------------- models
class ReadingIn(BaseModel):
    tag_id: int
    seq: Optional[int] = None
    ts: Optional[datetime] = None
    temp_c: Optional[float] = Field(None, ge=20, le=50)
    rumination_min: Optional[int] = Field(None, ge=0, le=15)
    activity_mg: Optional[int] = Field(None, ge=0, le=20000)
    battery_mv: Optional[int] = Field(None, ge=0, le=5100)
    flags: int = 0
    rssi: Optional[int] = None


class IngestIn(BaseModel):
    gateway_id: str
    readings: List[ReadingIn] = Field(..., max_length=2000)


class FarmIn(BaseModel):
    name: str
    owner_phone: Optional[str] = None
    language: str = "en"


class CowIn(BaseModel):
    tag_id: int
    farm_id: Optional[int] = None
    name: Optional[str] = None
    breed: Optional[str] = None
    last_insemination: Optional[str] = None


class CowPatch(BaseModel):
    farm_id: Optional[int] = None
    name: Optional[str] = None
    breed: Optional[str] = None
    last_insemination: Optional[str] = None


# ---------------------------------------------------------------- app
def create_app(db_path: Optional[str] = None) -> FastAPI:
    db = DB(db_path or settings.db_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = None
        if not os.environ.get("CH_DISABLE_SWEEPER"):
            async def loop():
                while True:
                    await asyncio.sleep(600)
                    try:
                        app.state.sweep()
                    except Exception as e:
                        log.warning("sweep failed: %s", e)
            task = asyncio.create_task(loop())
        yield
        if task:
            task.cancel()

    app = FastAPI(title="CattleHealth AI", version=__version__, lifespan=lifespan)
    app.state.db = db

    def require_api_key(x_api_key: Optional[str] = Header(None)):
        if settings.api_key and x_api_key != settings.api_key:
            raise HTTPException(401, "invalid API key")

    def require_gateway(x_gateway_key: Optional[str] = Header(None)):
        if x_gateway_key not in settings.gateway_keys:
            raise HTTPException(401, "invalid gateway key")

    def readings_for(tag_id: int, since: datetime) -> List[dict]:
        rows = db.query("SELECT * FROM readings WHERE tag_id=? AND ts>=? ORDER BY ts", (tag_id, iso(since)))
        for r in rows:
            r["ts"] = parse_ts(r["ts"])
        return rows

    def cow_summary(cow: dict, now: datetime) -> dict:
        rs = readings_for(cow["tag_id"], now - timedelta(days=HISTORY_DAYS))
        findings = evaluate(rs, now) if rs else []
        last = rs[-1] if rs else None
        rum = daily_rumination(rs, now) if rs else None
        return {
            **cow,
            "status": status_from(findings) if rs else "no_data",
            "findings": [{"kind": f.kind, "severity": f.severity, "value": f.value} for f in findings],
            "last_seen": iso(last["ts"]) if last else None,
            "temp_c": last["temp_c"] if last else None,
            "baseline_c": temp_baseline(rs, now) if rs else None,
            "rumination_24h": round(rum) if rum is not None else None,
            "activity_mg": last["activity_mg"] if last else None,
            "battery_mv": last["battery_mv"] if last else None,
            "rssi": last["rssi"] if last else None,
        }

    # ------------------------------------------------------------ ingest
    @app.post("/api/v1/ingest", dependencies=[Depends(require_gateway)])
    def ingest(body: IngestIn):
        now = utcnow()
        gw = db.one("SELECT * FROM gateways WHERE id=?", (body.gateway_id,))
        with db.tx() as c:
            if gw:
                c.execute("UPDATE gateways SET last_seen=? WHERE id=?", (iso(now), body.gateway_id))
            else:
                c.execute("INSERT INTO gateways(id, last_seen) VALUES(?,?)", (body.gateway_id, iso(now)))
        farm_id = gw["farm_id"] if gw else None

        accepted, dupes, touched = 0, 0, {}
        with db.tx() as c:
            for r in body.readings:
                ts = (r.ts.astimezone(timezone.utc) if r.ts and r.ts.tzinfo else (r.ts.replace(tzinfo=timezone.utc) if r.ts else now))
                if ts > now + timedelta(minutes=10):
                    ts = now
                c.execute("INSERT OR IGNORE INTO cows(tag_id, farm_id) VALUES(?,?)", (r.tag_id, farm_id))
                cur = c.execute(
                    "INSERT OR IGNORE INTO readings(tag_id,seq,ts,temp_c,rumination_min,activity_mg,battery_mv,flags,rssi,gateway_id)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (r.tag_id, r.seq, iso(ts), r.temp_c, r.rumination_min, r.activity_mg, r.battery_mv, r.flags, r.rssi, body.gateway_id))
                if cur.rowcount:
                    accepted += 1
                    touched[r.tag_id] = max(touched.get(r.tag_id, ts), ts)
                else:
                    dupes += 1

        new_alerts = []
        for tag, latest in touched.items():
            rs = readings_for(tag, latest - timedelta(days=HISTORY_DAYS))
            findings = [f for f in evaluate(rs, latest) if f.kind != "offline"]
            new_alerts += raise_alerts(db, tag, findings, latest)
        return {"accepted": accepted, "duplicates": dupes, "alerts": new_alerts}

    # ------------------------------------------------------------ farms & cows
    @app.get("/api/v1/farms", dependencies=[Depends(require_api_key)])
    def list_farms():
        return db.query("SELECT * FROM farms ORDER BY id")

    @app.post("/api/v1/farms", dependencies=[Depends(require_api_key)], status_code=201)
    def create_farm(f: FarmIn):
        if f.language not in LANGS:
            raise HTTPException(422, f"language must be one of {LANGS}")
        with db.tx() as c:
            cur = c.execute("INSERT INTO farms(name, owner_phone, language) VALUES(?,?,?)", (f.name, f.owner_phone, f.language))
        return db.one("SELECT * FROM farms WHERE id=?", (cur.lastrowid,))

    @app.post("/api/v1/gateways/{gateway_id}/farm/{farm_id}", dependencies=[Depends(require_api_key)])
    def assign_gateway(gateway_id: str, farm_id: int):
        with db.tx() as c:
            c.execute("INSERT INTO gateways(id, farm_id) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET farm_id=excluded.farm_id", (gateway_id, farm_id))
            c.execute("UPDATE cows SET farm_id=? WHERE farm_id IS NULL AND tag_id IN (SELECT DISTINCT tag_id FROM readings WHERE gateway_id=?)", (farm_id, gateway_id))
        return {"gateway_id": gateway_id, "farm_id": farm_id}

    @app.get("/api/v1/cows", dependencies=[Depends(require_api_key)])
    def list_cows(farm_id: Optional[int] = None):
        now = utcnow()
        cows = db.query("SELECT * FROM cows WHERE (? IS NULL OR farm_id=?) ORDER BY tag_id", (farm_id, farm_id))
        return [cow_summary(c, now) for c in cows]

    @app.post("/api/v1/cows", dependencies=[Depends(require_api_key)], status_code=201)
    def create_cow(c: CowIn):
        with db.tx() as con:
            con.execute("INSERT INTO cows(tag_id, farm_id, name, breed, last_insemination) VALUES(?,?,?,?,?) "
                        "ON CONFLICT(tag_id) DO UPDATE SET farm_id=COALESCE(excluded.farm_id, farm_id), "
                        "name=COALESCE(excluded.name, name), breed=COALESCE(excluded.breed, breed), "
                        "last_insemination=COALESCE(excluded.last_insemination, last_insemination)",
                        (c.tag_id, c.farm_id, c.name, c.breed, c.last_insemination))
        return db.one("SELECT * FROM cows WHERE tag_id=?", (c.tag_id,))

    @app.patch("/api/v1/cows/{tag_id}", dependencies=[Depends(require_api_key)])
    def patch_cow(tag_id: int, p: CowPatch):
        if not db.one("SELECT tag_id FROM cows WHERE tag_id=?", (tag_id,)):
            raise HTTPException(404, "cow not found")
        fields = {k: v for k, v in p.model_dump().items() if v is not None}
        if fields:
            with db.tx() as c:
                c.execute(f"UPDATE cows SET {', '.join(k + '=?' for k in fields)} WHERE tag_id=?", (*fields.values(), tag_id))
        return db.one("SELECT * FROM cows WHERE tag_id=?", (tag_id,))

    @app.get("/api/v1/cows/{tag_id}", dependencies=[Depends(require_api_key)])
    def cow_detail(tag_id: int, hours: int = Query(72, ge=1, le=24 * 30)):
        cow = db.one("SELECT * FROM cows WHERE tag_id=?", (tag_id,))
        if not cow:
            raise HTTPException(404, "cow not found")
        now = utcnow()
        rs = readings_for(tag_id, now - timedelta(days=max(HISTORY_DAYS, hours / 24 + 1)))
        daily = []
        for i in range(6, -1, -1):
            end = (now - timedelta(days=i))
            v = daily_rumination(rs, end)
            daily.append({"date": end.strftime("%Y-%m-%d"), "rumination_min": round(v) if v is not None else None})
        series = [{"ts": iso(r["ts"]), "temp_c": r["temp_c"], "rumination_min": r["rumination_min"],
                   "activity_mg": r["activity_mg"]} for r in rs if r["ts"] >= now - timedelta(hours=hours)]
        alerts = db.query("SELECT * FROM alerts WHERE tag_id=? ORDER BY created_at DESC LIMIT 50", (tag_id,))
        return {**cow_summary(cow, now), "series": series, "daily_rumination": daily, "alerts": alerts}

    # ------------------------------------------------------------ alerts
    @app.get("/api/v1/alerts", dependencies=[Depends(require_api_key)])
    def list_alerts(active: bool = False, farm_id: Optional[int] = None, limit: int = Query(100, le=1000)):
        return db.query(
            "SELECT a.*, c.name AS cow_name, c.farm_id FROM alerts a LEFT JOIN cows c ON c.tag_id=a.tag_id "
            "WHERE (?=0 OR a.acknowledged=0) AND (? IS NULL OR c.farm_id=?) ORDER BY a.created_at DESC LIMIT ?",
            (int(active), farm_id, farm_id, limit))

    @app.post("/api/v1/alerts/{alert_id}/ack", dependencies=[Depends(require_api_key)])
    def ack_alert(alert_id: int):
        with db.tx() as c:
            cur = c.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
        if not cur.rowcount:
            raise HTTPException(404, "alert not found")
        return {"id": alert_id, "acknowledged": True}

    def sweep(now: Optional[datetime] = None) -> List[dict]:
        """Periodic check for offline tags (and anything else time-based)."""
        now = now or utcnow()
        out = []
        for cow in db.query("SELECT tag_id FROM cows"):
            rs = readings_for(cow["tag_id"], now - timedelta(days=HISTORY_DAYS))
            if rs:
                out += raise_alerts(db, cow["tag_id"], [f for f in evaluate(rs, now) if f.kind == "offline"], now)
        return out

    app.state.sweep = sweep

    @app.post("/api/v1/sweep", dependencies=[Depends(require_api_key)])
    def sweep_endpoint():
        return {"alerts": sweep()}

    # ------------------------------------------------------------ WhatsApp webhook
    @app.get("/webhook/whatsapp")
    def wa_verify(request: Request):
        q = request.query_params
        if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == settings.wa_verify_token:
            return PlainTextResponse(q.get("hub.challenge", ""))
        raise HTTPException(403, "verification failed")

    @app.post("/webhook/whatsapp")
    async def wa_incoming(request: Request):
        """Farmers can send any message (e.g. 'status') to get a herd summary back."""
        data = await request.json()
        now = utcnow()
        try:
            for entry in data.get("entry", []):
                for ch in entry.get("changes", []):
                    for m in ch.get("value", {}).get("messages", []):
                        phone = m.get("from", "")
                        farm = db.one("SELECT * FROM farms WHERE owner_phone=?", (phone,))
                        if not farm:
                            continue
                        cows = [cow_summary(c, now) for c in db.query("SELECT * FROM cows WHERE farm_id=?", (farm["id"],))]
                        bad = [c for c in cows if c["status"] in ("warning", "critical", "heat")]
                        text = render("summary", farm["language"], farm=farm["name"], n=len(cows),
                                      ok=len(cows) - len(bad), alerts=len(bad))
                        for c in bad:
                            for f in c["findings"]:
                                text += f"\n• {c['name'] or 'Cow #' + str(c['tag_id'])}: {f['kind']} ({f['value']})"
                        send_whatsapp(phone, text)
        except Exception as e:  # never make Meta retry-storm us
            log.warning("webhook parse error: %s", e)
        return {"ok": True}

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "version": __version__}

    dash = os.environ.get("CH_DASHBOARD_DIR") or os.path.join(os.path.dirname(__file__), "..", "..", "dashboard")
    if os.path.isdir(dash):
        app.mount("/", StaticFiles(directory=dash, html=True), name="dashboard")
    return app


app = create_app()
