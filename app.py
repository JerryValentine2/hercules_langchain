"""Hercules LangChain v1: default Vertex AI Gemini, optional external endpoint."""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP

LOG = logging.getLogger("hercules_langchain")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())


def load_config() -> dict:
    path = Path(os.getenv("HERCULES_CONFIG", "config.yaml"))
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("hercules"), dict):
        raise ValueError("config.yaml requires a hercules mapping")
    return config["hercules"]


CONFIG = load_config()
mcp = FastMCP(
    "hercules_langchain",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8080")),
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)


def build_model(path: str):
    if path == "gemini":
        from langchain_google_vertexai import ChatVertexAI
        settings = CONFIG.get("gemini", {})
        model = os.getenv("GEMINI_MODEL", settings.get("model", "gemini-2.5-flash"))
        location = os.getenv("GOOGLE_CLOUD_LOCATION", settings.get("location", "us-central1"))
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        kwargs = {"model": model, "location": location, "max_retries": 0}
        if project:
            kwargs["project"] = project
        return ChatVertexAI(**kwargs), model
    if path == "external":
        from langchain_openai import ChatOpenAI
        settings = CONFIG.get("external", {})
        model = os.getenv("EXTERNAL_MODEL") or settings.get("model")
        base_url = os.getenv("EXTERNAL_BASE_URL") or settings.get("base_url")
        api_key = os.getenv("EXTERNAL_API_KEY")
        if not all((model, base_url, api_key)):
            raise ValueError("External path requires EXTERNAL_MODEL, EXTERNAL_BASE_URL, and EXTERNAL_API_KEY")
        return ChatOpenAI(model=model, base_url=base_url, api_key=api_key, max_retries=0), model
    raise ValueError("Unsupported path: use gemini or external")


def run_message(message: Any, product_id: str | None = None, path: str | None = None) -> dict[str, str]:
    if not isinstance(message, str) or not message.strip():
        return {"status": "error", "error": "message must be a non-empty string"}
    if product_id is not None and not isinstance(product_id, str):
        return {"status": "error", "error": "product_id must be a string when supplied"}
    selected = path if path is not None else CONFIG.get("default_path", "gemini")
    if selected not in ("gemini", "external"):
        return {"status": "error", "error": "path must be gemini or external"}
    started = time.monotonic()
    try:
        llm, model_name = build_model(selected)
        result = llm.invoke(message)
        answer = result.content
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Model returned no usable text")
        LOG.info("model_completed path=%s duration_ms=%d", selected, round((time.monotonic() - started) * 1000))
        return {"status": "success", "model": model_name, "answer": answer}
    except Exception as exc:
        LOG.warning("model_failed path=%s type=%s duration_ms=%d", selected, type(exc).__name__, round((time.monotonic() - started) * 1000))
        return {"status": "error", "error": f"Model invocation failed ({type(exc).__name__})"}


@mcp.tool()
def run_langchain(message: str, product_id: str | None = None, path: str | None = None) -> dict[str, str]:
    """Invoke default Gemini or optional external OpenAI-compatible endpoint."""
    return run_message(message, product_id, path)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
