"""app.services.langfuse_service

Langfuse Service
----------------
Centralizes Langfuse initialization + helper utilities.

This version adds **collective/batch RCA** helpers:
  - Stable 30-minute *batch session ids* (so each cron run groups in Langfuse)
  - A context manager that starts a Langfuse span and propagates the session_id

Use-case: every 30 minutes, you run ONE LLM call for the whole metrics batch.
You want that whole run (batch span + LLM generation) under ONE Langfuse session.
"""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, Optional, Tuple

from app.core.config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
from app.core.logging import logger

try:
    # Langfuse v3.12+ API
    from langfuse import Langfuse, get_client, propagate_attributes, observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    propagate_attributes = None  # type: ignore
    observe = None  # type: ignore
    logger.info("[Langfuse] ⚠️ Not installed")


langfuse = None
LANGFUSE_ENABLED = False


def initialize_langfuse():
    """Initialize Langfuse client"""
    global langfuse, LANGFUSE_ENABLED

    if not LANGFUSE_AVAILABLE:
        logger.info("[Langfuse] ⚠️ Not installed")
        return

    if not (LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY):
        logger.info("[Langfuse] ⚠️ Disabled (API keys not set in .env)")
        return

    try:
        Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
        langfuse = get_client()
        langfuse.auth_check()
        LANGFUSE_ENABLED = True
        logger.info("[Langfuse] ✅ v3.12+ Connected successfully!")
    except Exception as e:
        logger.error(f"[Langfuse] ❌ Failed to initialize: {e}")
        langfuse = None
        LANGFUSE_ENABLED = False


def get_langfuse_client():
    """Get Langfuse client instance"""
    return langfuse if LANGFUSE_ENABLED else None


def is_langfuse_enabled() -> bool:
    """Check if Langfuse is enabled and available"""
    return LANGFUSE_ENABLED


def flush_langfuse():
    """Flush remaining Langfuse data"""
    if langfuse and LANGFUSE_ENABLED:
        try:
            logger.info("[Langfuse] Flushing remaining data...")
            langfuse.flush()
            logger.info("[Langfuse] ✅ Flush complete")
        except Exception as e:
            logger.warning(f"[Langfuse] Flush error: {e}")


# ==========================
# Collective RCA helpers
# ==========================

def _floor_to_interval(dt: datetime, minutes: int) -> datetime:
    """Floor a UTC datetime to the start of its interval (minutes)."""
    if minutes <= 0:
        return dt.replace(second=0, microsecond=0)
    minute_bucket = (dt.minute // minutes) * minutes
    return dt.replace(minute=minute_bucket, second=0, microsecond=0)


def make_batch_window(now_utc: Optional[datetime] = None, interval_minutes: int = 30) -> Tuple[datetime, datetime]:
    """Return (window_start, window_end) for the current batch window in UTC."""
    now = now_utc or datetime.utcnow()
    start = _floor_to_interval(now, interval_minutes)
    end = start + timedelta(minutes=interval_minutes)
    return start, end


def make_batch_session_id(
    now_utc: Optional[datetime] = None,
    interval_minutes: int = 30,
    prefix: str = "batch",
) -> str:
    """Stable session id for a batch run.

    Example (interval=30min):
      batch:202601281200-202601281230
    """
    start, end = make_batch_window(now_utc=now_utc, interval_minutes=interval_minutes)
    return f"{prefix}:{start.strftime('%Y%m%d%H%M')}-{end.strftime('%Y%m%d%H%M')}"


@contextmanager
def langfuse_session(session_id: Optional[str]) -> Iterator[None]:
    """Propagate a session_id into downstream Langfuse observations.

    This makes all nested spans/generations show up under the same session.
    """
    if not (session_id and LANGFUSE_ENABLED and propagate_attributes):
        yield
        return

    ctx = propagate_attributes(session_id=session_id)
    try:
        ctx.__enter__()
        yield
    finally:
        try:
            ctx.__exit__(None, None, None)
        except Exception:
            pass


@contextmanager
def start_span(
    name: str,
    *,
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    as_type: str = "span",
) -> Iterator[Optional[Any]]:
    """Start a Langfuse observation span (or no-op if disabled).

    Use this in your 30-minute batch cron:
      session_id = make_batch_session_id(...)
      with start_span("Batch Monitoring", session_id=session_id, metadata={...}) as span:
          ...
          # call ask_llm(..., session_id=session_id)
    """
    lf = get_langfuse_client()
    if not (lf and LANGFUSE_ENABLED):
        yield None
        return

    obs_ctx = None
    span_obj = None
    try:
        obs_ctx = lf.start_as_current_observation(
            as_type=as_type,
            name=name,
            metadata={**(metadata or {}), **({"session_id": session_id} if session_id else {})},
        )
        span_obj = obs_ctx.__enter__()
        with langfuse_session(session_id):
            yield span_obj
    except Exception as e:
        logger.warning(f"[Langfuse] start_span failed: {e}")
        yield None
    finally:
        if obs_ctx is not None:
            try:
                obs_ctx.__exit__(None, None, None)
            except Exception:
                pass
