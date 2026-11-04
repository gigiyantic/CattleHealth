import os
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass
class Settings:
    db_path: str = field(default_factory=lambda: _env("CH_DB_PATH", "cattlehealth.db"))
    # comma separated gateway keys accepted on /ingest
    gateway_keys: tuple = field(default_factory=lambda: tuple(k.strip() for k in _env("CH_GATEWAY_KEYS", "dev-gateway-key").split(",") if k.strip()))
    # dashboard / admin API key (empty = open, for local demos)
    api_key: str = field(default_factory=lambda: _env("CH_API_KEY", ""))
    # WhatsApp Cloud API (Meta). Leave empty for dry-run (alerts are logged only).
    wa_token: str = field(default_factory=lambda: _env("WHATSAPP_TOKEN", ""))
    wa_phone_id: str = field(default_factory=lambda: _env("WHATSAPP_PHONE_NUMBER_ID", ""))
    wa_verify_token: str = field(default_factory=lambda: _env("WHATSAPP_VERIFY_TOKEN", "cattlehealth-verify"))
    wa_api_version: str = field(default_factory=lambda: _env("WHATSAPP_API_VERSION", "v21.0"))
    alert_cooldown_h: float = field(default_factory=lambda: float(_env("CH_ALERT_COOLDOWN_H", "12")))


settings = Settings()
