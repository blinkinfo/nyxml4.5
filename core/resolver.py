"""Gamma API poller — checks whether a 5-min slot has resolved (WIN / LOSS)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
import config as cfg

log = logging.getLogger(__name__)

MAX_POLL_ATTEMPTS = 20
POLL_INTERVAL = 15  # seconds between retries


async def check_resolution(slug: str) -> tuple[str | None, bool]:
    """Single check — hit Gamma API and inspect outcomePrices.

    Returns (winning_side, True) if resolved, (None, False) if still open.
    """
    url = f"{cfg.GAMMA_API_HOST}/markets"
    params = {"slug": slug}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        log.exception("Gamma API error while resolving slug=%s", slug)
        return None, False

    if not data or not isinstance(data, list) or len(data) == 0:
        return None, False

    market = data[0]
    try:
        outcomes = market["outcomes"]
        prices = [float(p) for p in market["outcomePrices"]]
    except (KeyError, ValueError, IndexError):
        log.exception("Parse error for slug=%s", slug)
        return None, False

    # Resolved when one side = 1.00 and the other = 0.00
    for idx, price in enumerate(prices):
        if price >= 0.99:
            winner = outcomes[idx]
            log.info("Slot %s resolved: winner=%s", slug, winner)
            return winner, True

    return None, False


async def resolve_slot(slug: str) -> str | None:
    """Poll until the slot resolves or we exhaust retries.

    Returns the winning side ("Up" or "Down") or None if unresolved.
    """
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        winner, resolved = await check_resolution(slug)
        if resolved:
            return winner
        log.debug("Slot %s not yet resolved (attempt %d/%d)", slug, attempt, MAX_POLL_ATTEMPTS)
        if attempt < MAX_POLL_ATTEMPTS:
            await asyncio.sleep(POLL_INTERVAL)

    log.warning("Slot %s did not resolve after %d attempts", slug, MAX_POLL_ATTEMPTS)
    return None
