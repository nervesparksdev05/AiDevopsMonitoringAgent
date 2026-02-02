from __future__ import annotations

import os
import requests
from typing import Optional, Tuple
from datetime import datetime

# ✅ OpenAI support (commented out)
# from openai import OpenAI

from app.services.langfuse_service import (
    get_langfuse_client,
    is_langfuse_enabled,
    langfuse_session,
)
from app.core.logging import logger

TIMEOUT_S = 120


def ask_llm(
    prompt: str,
    trace_name: str = "LLM Call",
    metadata: dict | None = None,
    session_id: Optional[str] = None,
) -> Optional[Tuple[str, int]]:
    """
    LLM call with optional Langfuse tracing.
    Supports Gemma3 (default) or OpenAI (commented out).
    
    Current config (Gemma3):
      - LLM_URL: Ollama/LM Studio endpoint
      - LLM_MODEL: Model name (default: gemma3:1b)
    
    OpenAI config (commented):
      - OPENAI_API_KEY
      - OPENAI_MODEL (default: gpt-4.1-mini)
    
    Returns: (response_text, total_tokens)
    """

    # ===== GEMMA3 CONFIGURATION (ACTIVE) =====
    llm_url = (os.getenv("LLM_URL") or "").strip()
    model = (os.getenv("LLM_MODEL") or "gemma3:1b").strip()
    provider = "gemma3"

    if not llm_url:
        logger.error("[LLM] LLM_URL not set")
        return None, 0

    logger.info(
        f"[LLM] Gemma3 model={model} | url={llm_url} | timeout={TIMEOUT_S}s | "
        f"prompt_chars={len(prompt or '')} words={len((prompt or '').split())}"
    )

    # ===== OPENAI CONFIGURATION (COMMENTED) =====
    # api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    # model = (os.getenv("OPENAI_MODEL") or "gpt-4.1-mini").strip()
    # provider = "openai"
    #
    # if not api_key:
    #     logger.error("[LLM] OPENAI_API_KEY not set")
    #     return None, 0
    #
    # logger.info(
    #     f"[LLM] OpenAI model={model} | timeout={TIMEOUT_S}s | "
    #     f"prompt_chars={len(prompt or '')} words={len((prompt or '').split())}"
    # )
    #
    # client = OpenAI(api_key=api_key)

    def _call_llm_gemma3() -> tuple[str, int, int, float]:
        """
        Gemma3/Ollama API call.
        Returns: (text, input_tokens, output_tokens, latency_ms)
        """
        start_time = datetime.utcnow()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                # "num_predict": 800,  # max tokens
            }
        }

        response = requests.post(
            f"{llm_url}/api/generate",
            json=payload,
            timeout=TIMEOUT_S
        )
        response.raise_for_status()

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        result = response.json()
        text = (result.get("response", "") or "").strip()

        # Gemma3/Ollama token counts
        input_tokens = int(result.get("prompt_eval_count", 0) or 0)
        output_tokens = int(result.get("eval_count", 0) or 0)

        return text, input_tokens, output_tokens, latency_ms

    # def _call_llm_openai() -> tuple[str, int, int, float]:
    #     """
    #     OpenAI API call (COMMENTED).
    #     Returns: (text, input_tokens, output_tokens, latency_ms)
    #     """
    #     start_time = datetime.utcnow()
    #
    #     resp = client.responses.create(
    #         model=model,
    #         input=prompt,
    #         temperature=0.2,
    #         # max_output_tokens=800,
    #     )
    #
    #     latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    #
    #     text = (getattr(resp, "output_text", "") or "").strip()
    #
    #     usage = getattr(resp, "usage", None)
    #     input_tokens = int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
    #     output_tokens = int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
    #
    #     return text, input_tokens, output_tokens, latency_ms

    langfuse = get_langfuse_client()

    # -------- traced path --------
    if langfuse and is_langfuse_enabled():
        try:
            with langfuse.start_as_current_observation(
                as_type="span",
                name=trace_name,
                metadata={
                    **(metadata or {}),
                    "model": model,
                    "provider": provider,
                    "timeout_s": TIMEOUT_S,
                    **({"session_id": session_id} if session_id else {}),
                },
            ) as root_span:
                with langfuse_session(session_id):
                    with langfuse.start_as_current_observation(
                        as_type="generation",
                        name="llm-generation",
                        model=model,
                        input=prompt,
                    ) as generation:
                        try:
                            logger.info(
                                f"[LLM] Calling {provider.upper()}..."
                                + (f" (session: {session_id})" if session_id else "")
                            )

                            # ===== ACTIVE: Gemma3 =====
                            text, in_tok, out_tok, latency_ms = _call_llm_gemma3()
                            
                            # ===== COMMENTED: OpenAI =====
                            # text, in_tok, out_tok, latency_ms = _call_llm_openai()
                            
                            logger.info(f"[LLM] Response received ({latency_ms:.0f}ms)")

                            total_tokens = (
                                (in_tok + out_tok)
                                if (in_tok or out_tok)
                                else _estimate_tokens(prompt, text)
                            )

                            generation.update(
                                output=text,
                                usage={
                                    "input": in_tok,
                                    "output": out_tok,
                                    "total": total_tokens,
                                },
                                metadata={"latency_ms": latency_ms, "error": False},
                            )
                            root_span.update(output={"response": True, "tokens": total_tokens})
                            return text, total_tokens

                        except Exception as e:
                            logger.error(f"[LLM] Error: {e}", exc_info=True)
                            generation.update(output=f"Error: {str(e)}", metadata={"error": True})
                            root_span.update(output={"response": False, "error": str(e)})
                            return None, 0

        except Exception as e:
            logger.warning(f"[Langfuse] Error in tracing: {e}", exc_info=True)
            # fall through to fallback

    # -------- fallback path --------
    try:
        logger.info(f"[LLM] Calling {provider.upper()} (no tracing)...")
        
        # ===== ACTIVE: Gemma3 =====
        text, in_tok, out_tok, latency_ms = _call_llm_gemma3()
        
        # ===== COMMENTED: OpenAI =====
        # text, in_tok, out_tok, latency_ms = _call_llm_openai()
        
        logger.info(f"[LLM] Response received ({latency_ms:.0f}ms)")

        total_tokens = (in_tok + out_tok) if (in_tok or out_tok) else _estimate_tokens(prompt, text)
        return text, total_tokens

    except Exception as e:
        logger.error(f"[LLM] Error: {e}", exc_info=True)
        return None, 0


def _estimate_tokens(prompt: str, response_text: str) -> int:
    return int(len((prompt + "\n" + (response_text or "")).split()) * 1.3)