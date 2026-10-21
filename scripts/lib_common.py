"""Shared helpers: HTTP, normalisation, JSON, odds maths. Stdlib only."""
from __future__ import annotations

import gzip
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

UA = ("LOLHOTSPAWN2/3.0 (+https://github.com/karagemop466-tech/LOLHOTSPAWN2; "
      "open-source research bot; contact via GitHub issues)")
HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip",
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def log(msg: str) -> None:
    print(f"[{now_utc().isoformat(timespec='seconds')}] {msg}", file=sys.stderr, flush=True)


def fetch(url: str, headers: dict | None = None, timeout: int = 60, retries: int = 3) -> dict:
    """GET a URL. Returns {status, body(bytes), text, url, error}."""
    h = dict(HEADERS)
    if headers:
        h.update(headers)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                if body[:2] == b"\x1f\x8b":
                    try:
                        body = gzip.decompress(body)
                    except OSError:
                        pass
                return {"status": r.status, "body": body, "text": body.decode("utf-8", "replace"),
                        "url": url, "error": None}
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read()
            except Exception:
                pass
            if body[:2] == b"\x1f\x8b":
                try:
                    body = gzip.decompress(body)
                except OSError:
                    pass
            last = {"status": e.code, "body": body, "text": body.decode("utf-8", "replace"),
                    "url": url, "error": f"HTTP {e.code}"}
            if e.code in (400, 401, 403, 404):
                return last
        except Exception as e:  # noqa: BLE001 - network errors vary
            last = {"status": 0, "body": b"", "text": "", "url": url, "error": repr(e)[:200]}
        time.sleep(1.5 * (attempt + 1))
    return last


def get_json(url: str, headers: dict | None = None, timeout: int = 60, retries: int = 3):
    r = fetch(url, headers=headers, timeout=timeout, retries=retries)
    if r["status"] != 200:
        return None, r
    try:
        return json.loads(r["text"]), r
    except json.JSONDecodeError:
        return None, r


def norm(s) -> str:
    """ASCII-folded alphanumeric key used for fuzzy team matching."""
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def clean_name(s) -> str:
    """Display cleanup only; never invents information."""
    return re.sub(r"\s+", " ", str(s or "")).strip()


def parse_iso(s):
    if not s:
        return None
    try:
        if isinstance(s, (int, float)) or str(s).isdigit():
            v = float(s)
            if v > 1e12:
                v /= 1000.0
            return datetime.fromtimestamp(v, timezone.utc)
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def utc_iso(dt) -> str | None:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if dt else None


def decimal_from_american(price) -> float | None:
    try:
        p = float(price)
    except (TypeError, ValueError):
        return None
    if p > 0:
        return 1.0 + p / 100.0
    if p < 0:
        return 1.0 + 100.0 / abs(p)
    return None


def devig_two(dec_a, dec_b) -> tuple[float, float] | None:
    """Normalise two decimal prices to probabilities that sum to 1."""
    try:
        a, b = float(dec_a), float(dec_b)
    except (TypeError, ValueError):
        return None
    if a <= 1.0 or b <= 1.0:
        return None
    ia, ib = 1.0 / a, 1.0 / b
    s = ia + ib
    return ia / s, ib / s


def clamp(x: float, lo: float = 0.02, hi: float = 0.98) -> float:
    return max(lo, min(hi, x))


def prob_from_elo(r1: float, r2: float) -> float:
    return 1.0 / (1.0 + 10 ** ((r2 - r1) / 400.0))


def median(vals):
    vals = sorted(v for v in vals if v is not None)
    n = len(vals)
    if not n:
        return None
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0


def load_json(path: str, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def source(name: str, url: str, note: str = "", status: str = "ok") -> dict:
    return {"name": name, "url": url, "note": note, "status": status}


def days_between(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 86400.0


def exp_decay_value(value: float, days: float, half_life_days: float = 365.0) -> float:
    return value * math.exp(-math.log(2) * days / half_life_days)


def iso_week_start(dt: datetime) -> datetime:
    d = dt.astimezone(timezone.utc)
    return (d - timedelta(days=d.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
