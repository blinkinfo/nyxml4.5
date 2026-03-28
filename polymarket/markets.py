"""BTC 5-min slot helpers — compute slot boundaries & fetch prices from Gamma API."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
import config as cfg

log = logging.getLogger(__name__)

SLOT_DURATION = 300  # 5 minutes in seconds


# ---------------------------------------------------------------------------
# Slot boundary helpers
# ---------------------------------------------------------------------------

def _slot_start_ts(dt: datetime) -> int:
    """Return the unix timestamp of the current 5-min slot start for *dt*."""
    epoch = int(dt.timestamp())
    return epoch - (epoch % SLOT_DURATION)


def get_current_slot_info() -> dict[str, Any]:
    """Compute current slot N boundaries.

    Returns dict with:
      slot_start_dt, slot_end_dt, slot_start_ts, slug,
      slot_start_str ("HH:MM"), slot_end_str ("HH:MM")
    """
    now = datetime.now(timezone.utc)
    start_ts = _slot_start_ts(now)
    end_ts = start_ts + SLOT_DURATION
    start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_ts, tz=timezone.utc)
    slug = f"btc-updown-5m-{start_ts}"
    return {
        "slot_start_dt": start_dt,
        "slot_end_dt": end_dt,
        "slot_start_ts": start_ts,
        "slug": slug,
        "slot_start_str": start_dt.strftime("%H:%M"),
        "slot_end_str": end_dt.strftime("%H:%M"),
        "slot_start_full": start_dt.strftime("%Y-%m-%d %H:%M"),
        "slot_end_full": end_dt.strftime("%Y-%m-%d %H:%M"),
    }


def get_next_slot_info() -> dict[str, Any]:
    """Compute next slot N+1 boundaries."""
    now = datetime.now(timezone.utc)
    start_ts = _slot_start_ts(now) + SLOT_DURATION
    end_ts = start_ts + SLOT_DURATION
    start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_ts, tz=timezone.utc)
    slug = f"btc-updown-5m-{start_ts}"
    return {
        "slot_start_dt": start_dt,
        "slot_end_dt": end_dt,
        "slot_start_ts": start_ts,
        "slug": slug,
        "slot_start_str": start_dt.strftime("%H:%M"),
        "slot_end_str": end_dt.strftime("%H:%M"),
        "slot_start_full": start_dt.strftime("%Y-%m-%d %H:%M"),
        "slot_end_full": end_dt.strftime("%Y-%m-%d %H:%M"),
    }


def slot_info_from_ts(start_ts: int) -> dict[str, Any]:
    """Build slot info dict from an arbitrary start timestamp."""
    end_ts = start_ts + SLOT_DURATION
    start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_ts, tz=timezone.utc)
    slug = f"btc-updown-5m-{start_ts}"
    return {
        "slot_start_dt": start_dt,
        "slot_end_dt": end_dt,
        "slot_start_ts": start_ts,
        "slug": slug,
        "slot_start_str": start_dt.strftime("%H:%M"),
        "slot_end_str": end_dt.strftime("%H:%M"),
        "slot_start_full": start_dt.strftime("%Y-%m-%d %H:%M"),
        "slot_end_full": end_dt.strftime("%Y-%m-%d %H:%M"),
    }


# ---------------------------------------------------------------------------
# Gamma API price fetcher
# ---------------------------------------------------------------------------

async def get_slot_prices(slug: str) -> dict[str, Any] | None:
    """Fetch live prices & token IDs for a BTC 5-min slot from the Gamma API.

    GET https://gamma-api.polymarket.com/markets?slug={slug}

    Returns dict:
      up_price, down_price, up_token_id, down_token_id
    or None on error / empty response.
    """
    url = f"{cfg.GAMMA_API_HOST}/markets"
    params = {"slug": slug}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        log.exception("Gamma API request failed for slug=%s", slug)
        return None

    if not data or not isinstance(data, list) or len(data) == 0:
        log.warning("Gamma API returned empty response for slug=%s", slug)
        return None

    market = data[0]

    try:
        outcomes = market["outcomes"]
        prices_raw = market["outcomePrices"]
        token_ids_raw = market["clobTokenIds"]

        # outcomes = ["Up", "Down"] — map by name to be safe
        up_idx = outcomes.index("Up")
        down_idx = outcomes.index("Down")

        prices = [float(p) for p in prices_raw]
        token_ids = [str(t) for t in token_ids_raw]

        return {
            "up_price": prices[up_idx],
            "down_price": prices[down_idx],
            "up_token_id": token_ids[up_idx],
            "down_token_id": token_ids[down_idx],
        }
    except (KeyError, ValueError, IndexError):
        log.exception("Failed to parse Gamma market data for slug=%s", slug)
        return None
