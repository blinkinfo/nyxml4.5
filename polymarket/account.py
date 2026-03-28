"""Account helpers — balance, positions, connection status."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

log = logging.getLogger(__name__)


async def get_balance(poly_client) -> float | None:
    """Return USDC balance via the CLOB client (runs in thread to avoid blocking)."""
    try:
        result = await asyncio.to_thread(poly_client.client.get_balance_allowance)
        # result typically has 'balance' key in wei-string; convert to float USDC
        if isinstance(result, dict):
            raw = result.get("balance", "0")
            # Balance is returned in raw units (6 decimals for USDC)
            return round(float(raw) / 1e6, 2)
        return None
    except Exception:
        log.exception("Failed to fetch balance")
        return None


async def get_open_positions(poly_client) -> list[dict[str, Any]]:
    """Return list of open positions via the CLOB client."""
    try:
        positions = await asyncio.to_thread(poly_client.client.get_positions)
        if isinstance(positions, list):
            return positions
        return []
    except Exception:
        log.exception("Failed to fetch positions")
        return []


async def get_connection_status(poly_client) -> bool:
    """Quick connectivity check — try to hit the CLOB server info endpoint."""
    try:
        info = await asyncio.to_thread(poly_client.client.get_server_time)
        return info is not None
    except Exception:
        log.exception("Connection check failed")
        return False
