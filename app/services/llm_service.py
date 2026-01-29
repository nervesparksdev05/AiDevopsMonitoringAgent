"""
LLM Service - Minimal Version (Only What main.py Uses)
Handles LLM interactions with optional Langfuse tracing.
"""
from __future__ import annotations

import requests
from typing import Optional, Tuple
from datetime import datetime

from app.core.config import LLM_URL, LLM_MODEL
from app.services.langfuse_service import get_langfuse_client, is_langfuse_enabled, langfuse_session
from app.core.logging import logger


def ask_llm(
    prompt: str,
    trace_name: str = "LLM Call",
    metadata: dict | None = None,
    session_id: Optional[str] = None,
) -> Optional[Tuple[str, int]]:
    """
    Call LLM with optional Langfuse tracing.
    Returns (response_text, total_tokens) or (None, 0) on error.
    
    This is the ONLY function main.py uses from this file!
    """
    if not (LLM_URL or "").strip():
        logger.error("[LLM] LLM_URL not set")
        return None, 0

    langfuse = get_langfuse_client()
    response_text = None
    total_tokens = 0

    # With Langfuse tracing
    if langfuse and is_langfuse_enabled():
        try:
            with langfuse.start_as_current_observation(
                as_type="span",
                name=trace_name,
                metadata={
                    **(metadata or {}), 
                    "model": LLM_MODEL, 
                    "endpoint": LLM_URL, 
                    **({"session_id": session_id} if session_id else {})
                },
            ) as root_span:
                with langfuse_session(session_id):
                    with langfuse.start_as_current_observation(
                        as_type="generation",
                        name="llm-generation",
                        model=LLM_MODEL,
                        input=prompt,
                    ) as generation:
                        try:
                            log_msg = f"[LLM] Calling {LLM_URL}..."
                            if session_id:
                                log_msg += f" (session: {session_id})"
                            logger.info(log_msg)

                            start_time = datetime.utcnow()
                            resp = requests.post(
                                f"{LLM_URL}/api/generate",
                                json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
                                timeout=60,
                            )
                            end_time = datetime.utcnow()
                            latency_ms = (end_time - start_time).total_seconds() * 1000

                            logger.info(f"[LLM] Response received ({latency_ms:.0f}ms)")

                            if not resp.ok:
                                logger.error(f"[LLM] Error: HTTP {resp.status_code}")
                                generation.update(
                                    output=f"Error: HTTP {resp.status_code}",
                                    metadata={"error": True, "status_code": resp.status_code, "latency_ms": latency_ms},
                                )
                                return None, 0

                            response_text = resp.json().get("response", "") or ""

                            # Token estimate
                            input_tokens = int(len(prompt.split()) * 1.3)
                            output_tokens = int(len(response_text.split()) * 1.3)
                            total_tokens = input_tokens + output_tokens

                            generation.update(
                                output=response_text,
                                usage={"input": input_tokens, "output": output_tokens, "total": total_tokens},
                                metadata={"latency_ms": latency_ms, "error": False},
                            )

                            logger.info(f"[Langfuse] ✅ Logged generation ({total_tokens} tokens)")
                            
                        except requests.exceptions.Timeout:
                            logger.error("[LLM] Timeout after 60s")
                            generation.update(output="Error: Timeout", metadata={"error": True, "timeout": True})
                            return None, 0
                        except Exception as e:
                            logger.error(f"[LLM] Error: {e}")
                            generation.update(output=f"Error: {str(e)}", metadata={"error": True})
                            return None, 0

                root_span.update(output={"response": response_text, "tokens": total_tokens})
            return response_text, total_tokens
            
        except Exception as e:
            logger.warning(f"[Langfuse] Error in tracing: {e}")

    # Fallback without tracing
    try:
        logger.info(f"[LLM] Calling {LLM_URL} (no tracing)...")
        resp = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        if not resp.ok:
            logger.error(f"[LLM] Error: HTTP {resp.status_code}")
            return None, 0
        response_text = resp.json().get("response", "") or ""
        total_tokens = int(len((prompt + response_text).split()) * 1.3)
        return response_text, total_tokens
    except Exception as e:
        logger.error(f"[LLM] Error: {e}")
        return None, 0


# NOTE: These functions below are NOT used by main.py
# They exist for backward compatibility but can be removed if you want a cleaner codebase:
# - get_llm_analysis() - Never called
# - get_llm_batch_rca() - Never called  
# - _group_metrics_by_instance() - Never called
# - _render_metrics_for_prompt() - Never called
#
# main.py builds its own prompts directly in BatchMonitor.build_prompt()
# and calls ask_llm() directly via BatchMonitor.call_llm()