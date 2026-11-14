"""Shared helpers: paths, System Public Graph API client, request audit log."""
from __future__ import annotations

import json
import re
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TEAM_ROOT = ROOT.parent  # the teammate's repository root (Hackiller_V2PATH)
RESTORED = TEAM_ROOT / "data" / "restored" / "system"   # produced by scripts/restore_system.py (SHA-256 checked)
_RESTORED_ASSOC = RESTORED / "system-public-graph-v1-associations.csv"
RAW_CSV = _RESTORED_ASSOC if _RESTORED_ASSOC.exists() else DATA / "raw" / "system-public-graph-v1-associations.csv"
STUDIES_CSV = RESTORED / "system-public-graph-v1-studies.csv"
TEAM_PROCESSED = TEAM_ROOT / "data" / "processed"
INTERIM = DATA / "interim"
GRAPH = DATA / "graph"
VERIFIED = DATA / "verified"
SITE_DATA = ROOT / "site" / "data"
AUDIT_LOG = DATA / "request_log.jsonl"

BASE_URL = "https://public-api.system.com"


def _load_key() -> str:
    key = os.environ.get("SYSTEM_API_KEY")
    if not key:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("SYSTEM_API_KEY="):
                    key = line.split("=", 1)[1].strip()
    if not key:
        raise SystemExit("Set SYSTEM_API_KEY in the environment or in .env")
    return key


def log_request(source: str, url: str, params: dict | None, status: int, n: int | None) -> None:
    """Append one line per HTTP request (never includes credentials)."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a") as fh:
        fh.write(json.dumps({
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": source, "url": url, "params": params or {},
            "status": status, "records": n,
        }) + "\n")


class SystemAPI:
    """Minimal client for the System Public Graph v1 REST API."""

    def __init__(self, sleep_s: float = 0.05):
        self.session = requests.Session()
        self.session.headers["x-api-key"] = _load_key()
        self.sleep_s = sleep_s

    def get(self, path: str, params: dict | None = None):
        url = f"{BASE_URL}{path}"
        for attempt in range(4):
            resp = self.session.get(url, params=params or {}, timeout=60)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(1.5 * (attempt + 1))
                continue
            break
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None
        n = len(body.get("data", [])) if isinstance(body, dict) and "data" in body else None
        log_request("system", url, params, resp.status_code, n)
        resp.raise_for_status()
        time.sleep(self.sleep_s)
        return body

    def paginate(self, path: str, params: dict | None = None, page_size: int = 100,
                 max_records: int | None = None) -> list[dict]:
        """Walk an offset/limit list endpoint. Stops on an empty page (does not trust `total`)."""
        params = dict(params or {})
        params["limit"] = page_size
        out: list[dict] = []
        offset = 0
        while True:
            params["offset"] = offset
            page = self.get(path, params)
            rows = page.get("data", [])
            out.extend(rows)
            if len(rows) < page_size or (max_records and len(out) >= max_records):
                break
            offset += page_size
        return out[:max_records] if max_records else out


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str))


# Country name -> ISO 3166 alpha-3 (shared by all steps)
ISO3 = {
    "Benin": "BEN", "Burkina Faso": "BFA", "Burundi": "BDI", "Cameroon": "CMR", "Central African Republic": "CAF",
    "Chad": "TCD", "Congo": "COG", "Democratic Republic of the Congo": "COD", "Côte d'Ivoire": "CIV",
    "Equatorial Guinea": "GNQ", "Ethiopia": "ETH", "Gabon": "GAB", "Gambia": "GMB", "The Gambia": "GMB", "Ghana": "GHA",
    "Guinea-Bissau": "GNB", "Guinea": "GIN", "Kenya": "KEN", "Liberia": "LBR", "Madagascar": "MDG", "Malawi": "MWI",
    "Mali": "MLI", "Mauritania": "MRT", "Mozambique": "MOZ", "Niger": "NER", "Nigeria": "NGA", "Rwanda": "RWA",
    "Senegal": "SEN", "Sierra Leone": "SLE", "Somalia": "SOM", "South Sudan": "SSD", "Sudan": "SDN",
    "Tanzania": "TZA", "Togo": "TGO", "Uganda": "UGA", "Zambia": "ZMB", "Zimbabwe": "ZWE", "Angola": "AGO",
    "Eritrea": "ERI", "Namibia": "NAM", "India": "IND", "Myanmar": "MMR", "Cambodia": "KHM", "Laos": "LAO",
    "Vietnam": "VNM", "Thailand": "THA", "Indonesia": "IDN", "Papua New Guinea": "PNG", "Solomon Islands": "SLB",
    "Vanuatu": "VUT", "Bangladesh": "BGD", "Pakistan": "PAK", "Afghanistan": "AFG", "Sri Lanka": "LKA",
    "Brazil": "BRA", "Peru": "PER", "Colombia": "COL", "Venezuela": "VEN", "Haiti": "HTI", "Yemen": "YEM",
}


def to_iso3(text: str) -> str:
    """'Burkina Faso; Mali' or 'BFA;MLI' or 'multi-country' -> 'BFA;MLI' (unknown parts dropped)."""
    out = []
    for part in re.split(r"[;,]", text or ""):
        part = part.strip()
        code = part if re.fullmatch(r"[A-Z]{3}", part) else ISO3.get(part)
        if code and code not in out:
            out.append(code)
    return ";".join(out)
