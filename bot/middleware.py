"""Telegram auth middleware — restricts bot to a single chat ID."""

from __future__ import annotations

import functools
import logging
from typing import Callable

import config as cfg

log = logging.getLogger(__name__)


def auth_check(func: Callable) -> Callable:
    """Decorator that silently ignores updates from unauthorised chats.

    Compares ``update.effective_chat.id`` against ``TELEGRAM_CHAT_ID``.
    """

    @functools.wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        chat_id = update.effective_chat.id if update.effective_chat else None
        allowed = cfg.TELEGRAM_CHAT_ID
        if allowed is None:
            log.warning("TELEGRAM_CHAT_ID not set — rejecting all requests")
            return
        if str(chat_id) != str(allowed):
            log.debug("Ignoring update from chat_id=%s (allowed=%s)", chat_id, allowed)
            return
        return await func(update, context, *args, **kwargs)

    return wrapper
