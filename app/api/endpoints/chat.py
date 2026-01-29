"""
Chat Routes
AI chat endpoints with session management
"""
import asyncio
from fastapi import APIRouter
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.mongodb_service import get_db
from app.services.session_service import session_manager
from app.services.llm_service import ask_llm
from app.core.logging import logger

router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """
    Chat with AI assistant
    Maintains conversation context through sessions
    """
    db = get_db()

    session_id = message.session_id
    if not session_id or not session_manager.get_session(session_id, db):
        session_id = session_manager.create_session(db)
        logger.info(f"[Chat] New conversation session: {session_id}")
    else:
        logger.info(f"[Chat] Continuing session: {session_id}")

    context_str = ""
    if message.context:
        context_lines = ["Context:"]
        for k, v in message.context.items():
            if k != "session_id":
                context_lines.append(f"- {k}: {v}")
        context_str = "\n".join(context_lines)

    prompt = f"""You are a helpful DevOps assistant.
User asks: {message.message}

{context_str}

Provide a helpful, concise answer. Explain technical concepts simply if asked."""

    result = await asyncio.get_event_loop().run_in_executor(
        None,
        ask_llm,
        prompt,
        "AI Chat",
        {"user_message": message.message, **message.context},
        session_id,
    )

    response_text, tokens = result if result else (None, 0)
    session_manager.update_session(session_id, db, tokens)

    return {
        "response": response_text or "Sorry, I'm having trouble connecting to the AI service.",
        "session_id": session_id,
    }
