"""Hercules LangChain v1: MCP -> LangChain -> Gemini.

No inference is performed by this service without a successful Gemini call.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

from mcp.server.fastmcp import FastMCP

LOG = logging.getLogger("hercules_langchain")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
TIMEOUT_SECONDS = float(os.getenv("MODEL_TIMEOUT_SECONDS", "60"))
if not 0 < TIMEOUT_SECONDS <= 300:
    raise ValueError("MODEL_TIMEOUT_SECONDS must be between 0 and 300")
if not os.getenv("GOOGLE_API_KEY"):
    LOG.warning("GOOGLE_API_KEY is not set; requests will fail until configured")

mcp = FastMCP(
    "hercules_langchain",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8080")),
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)


def run_message(message: Any, product_id: str | None = None) -> dict[str, str]:
    """Execute one model request. product_id is reserved for future use."""
    if not isinstance(message, str) or not message.strip():
        return {"status": "error", "error": "message must be a non-empty string"}
    if product_id is not None and not isinstance(product_id, str):
        return {"status": "error", "error": "product_id must be a string when supplied"}
    if not os.getenv("GOOGLE_API_KEY"):
        return {"status": "error", "error": "Gemini provider credentials are not configured"}
    started = time.monotonic()
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model=MODEL,
            google_api_key=os.environ["GOOGLE_API_KEY"],
            timeout=TIMEOUT_SECONDS,
            max_retries=0,
        )
        result = llm.invoke(message)
        answer = result.content
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Gemini returned no usable text")
        LOG.info("gemini_completed duration_ms=%d", round((time.monotonic() - started) * 1000))
        return {"status": "success", "model": MODEL, "answer": answer}
    except Exception as exc:
        LOG.warning("gemini_failed type=%s duration_ms=%d", type(exc).__name__, round((time.monotonic() - started) * 1000))
        return {"status": "error", "error": f"Gemini invocation failed ({type(exc).__name__})"}


@mcp.tool()
def run_langchain(message: str, product_id: str | None = None) -> dict[str, str]:
    """Ask Gemini through LangChain and return a structured result."""
    return run_message(message, product_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
