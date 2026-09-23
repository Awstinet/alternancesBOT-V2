import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.local", override=True)


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"[CONFIG] Variable d'environnement obligatoire manquante : '{key}'\n"
        )
    return value


def _require_int(key: str) -> int:
    raw = _require(key)
    try:
        return int(raw)
    except ValueError:
        raise EnvironmentError(
            f"[CONFIG] '{key}' doit être un entier, valeur reçue : '{raw}'"
        )


def _optional(key: str, default: str = "") -> str: return os.getenv(key, default)


def _optional_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise EnvironmentError(
            f"[CONFIG] '{key}' doit être un entier, valeur reçue : '{raw}'"
        )


def _optional_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("true", "1", "yes")


def _optional_list(key: str, default: list[str] | None = None, sep: str = ",") -> list[str]:
    raw = os.getenv(key)
    if not raw:
        return default or []
    return [item.strip() for item in raw.split(sep) if item.strip()]


@dataclass(frozen=True)
class Config:

    DISCORD_BOT_TOKEN: str
    DISCORD_GUILD_ID: int
    DISCORD_CHANNEL_ID: int

    SCRAPING_INTERVAL_MINUTES: int
    SCRAPING_MAX_RESULTS: int
    LOCATION: str
    TOGGLE_SCRAPING: bool

    ENABLED_WEBSITES: list[str]
    
    DAYS_BEFORE_REVIVAL: int
    
    LINKEDIN_LOGIN: str
    LINKEDIN_PASSWORD: str


def _build_config() -> Config:
    return Config(
        DISCORD_BOT_TOKEN=_require("DISCORD_BOT_TOKEN"),
        DISCORD_GUILD_ID=_require_int("DISCORD_GUILD_ID"),
        DISCORD_CHANNEL_ID=_require_int("DISCORD_CHANNEL_ID"),

        SCRAPING_INTERVAL_MINUTES=_optional_int("SCRAPING_INTERVAL_MINUTES", default=60),
        SCRAPING_MAX_RESULTS=_optional_int("SCRAPING_MAX_RESULTS", default=10),
        LOCATION=_optional("DEFAULT_LOCATION", default="Paris"),
        TOGGLE_SCRAPING=_optional_bool("TOGGLE_SCRAPING", default=False),

        ENABLED_WEBSITES=_optional_list("ENABLED_WEBSITES", default=["linkedin", "indeed"]),
        
        DAYS_BEFORE_REVIVAL=_optional_int("DAYS_BEFORE_REVIVAL", default=3),
        
        LINKEDIN_LOGIN=_optional("LINKEDIN_LOGIN", default="None"),
        LINKEDIN_PASSWORD=_optional("LINKEDIN_PASSWORD", default="None"),
    )
    

config = _build_config()