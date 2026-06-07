import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

load_dotenv()

# ── Structured logger ──────────────────────────────────────────────
# Logs every agent event as a JSON line to both console and a file.
# JSON format means you can grep, filter, and analyse logs later.

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",       # just the message — we format it as JSON ourselves
    handlers=[
        logging.StreamHandler(),                          # print to console
        logging.FileHandler("logs/agent.log", mode="a")  # append to file
    ]
)

logger = logging.getLogger("nocodecode")


def log(agent: str, event: str, data: dict = None):
    """
    Write a structured JSON log entry.

    agent: which agent is logging (planner, coder, etc.)
    event: what happened (started, completed, error, etc.)
    data:  any extra context to include

    Example output:
    {"time":"2025-01-15T10:00:00","agent":"planner","event":"completed","data":{"language":"python"}}
    """
    entry = {
        "time":  datetime.utcnow().isoformat(),
        "agent": agent,
        "event": event,
        "data":  data or {}
    }
    logger.info(json.dumps(entry))


# ── LangFuse client ────────────────────────────────────────────────
# One global client for the whole app.
# LangFuse batches events and sends them to the cloud dashboard.

_langfuse_client = None


def get_langfuse_client() -> Langfuse:
    """
    Return the global LangFuse client, creating it once on first call.
    If keys are missing, returns None so the app still works without tracing.
    """
    global _langfuse_client

    if _langfuse_client is not None:
        return _langfuse_client

    public_key  = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key  = os.getenv("LANGFUSE_SECRET_KEY")
    host        = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        log("tracer", "langfuse_disabled", {"reason": "missing keys in .env"})
        return None

    _langfuse_client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host
    )
    return _langfuse_client


def get_langfuse_handler(session_id: str, task: str) -> CallbackHandler | None:
    """
    Return a LangChain-compatible LangFuse callback handler.

    This is what you pass to chain.invoke(..., config={"callbacks": [handler]}).
    LangChain automatically calls it before and after every LLM call,
    so LangFuse records the prompt, response, tokens, and latency
    without you having to add timing code everywhere.

    session_id: links this trace to a user session
    task:       the user's original request — shown as trace name in dashboard
    """

    client = get_langfuse_client()
    if client is None:
        return None

    return CallbackHandler()


def flush():
    """
    Force LangFuse to send any buffered events immediately.
    Call this on app shutdown so no events are lost.
    LangFuse normally batches events to reduce API calls.
    """
    client = get_langfuse_client()
    if client:
        client.flush()