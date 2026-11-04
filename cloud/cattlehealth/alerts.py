"""Turn findings into stored alerts (with cooldown) and deliver them over WhatsApp."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List

import httpx

from .config import settings
from .db import DB
from .detection import Finding
from .messages import render

log = logging.getLogger("cattlehealth.alerts")


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def send_whatsapp(to: str, text: str) -> bool:
    """Send a text via the WhatsApp Cloud API. Dry-run (log only) when not configured."""
    if not (settings.wa_token and settings.wa_phone_id and to):
        log.info("[whatsapp dry-run] to=%s %s", to or "-", text)
        return False
    url = f"https://graph.facebook.com/{settings.wa_api_version}/{settings.wa_phone_id}/messages"
    try:
        r = httpx.post(url, timeout=10, headers={"Authorization": f"Bearer {settings.wa_token}"},
                       json={"messaging_product": "whatsapp", "to": to, "type": "text",
                             "text": {"preview_url": False, "body": text}})
        if r.status_code >= 300:
            log.warning("whatsapp send failed %s: %s", r.status_code, r.text[:300])
            return False
        return True
    except httpx.HTTPError as e:
        log.warning("whatsapp send error: %s", e)
        return False


def raise_alerts(db: DB, tag_id: int, findings: List[Finding], now: datetime, notify: bool = True) -> List[dict]:
    """Store new alerts, skipping kinds already alerted for this cow within the cooldown."""
    if not findings:
        return []
    cow = db.one("SELECT c.tag_id, c.name, f.owner_phone, f.language FROM cows c "
                 "LEFT JOIN farms f ON f.id = c.farm_id WHERE c.tag_id = ?", (tag_id,)) or {}
    name = cow.get("name") or f"Cow #{tag_id}"
    lang = cow.get("language") or "en"
    since = iso(now - timedelta(hours=settings.alert_cooldown_h))
    created = []
    for f in findings:
        if db.one("SELECT id FROM alerts WHERE tag_id=? AND kind=? AND created_at>=?", (tag_id, f.kind, since)):
            continue
        msg = render(f.kind, lang, cow=name, **f.params)
        sent = send_whatsapp(cow.get("owner_phone") or "", msg) if notify else False
        with db.tx() as c:
            cur = c.execute("INSERT INTO alerts(tag_id,kind,severity,message,value,created_at,sent_whatsapp) "
                            "VALUES(?,?,?,?,?,?,?)", (tag_id, f.kind, f.severity, msg, f.value, iso(now), int(sent)))
        created.append({"id": cur.lastrowid, "tag_id": tag_id, "kind": f.kind, "severity": f.severity,
                        "message": msg, "value": f.value, "created_at": iso(now)})
    return created
