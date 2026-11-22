# Hercules LangChain — v1.0.0 MVP

One working implementation path: **ChatGPT MCP client → Cloud Run HTTPS `/mcp` → Python MCP server → LangChain → Gemini → MCP response**.

The existing local Hercules execution engine is separate and unchanged. No MAS or agent orchestration is included.

## Tool

`run_langchain(message: str, product_id: str | None = None)`

Success: `{"status":"success","model":"gemini-2.5-flash","answer":"..."}`

Failure: `{"status":"error","error":"..."}`. The service never returns a fabricated model answer.

## Local run

Requires Python 3.11+ and a valid Gemini API key.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
python app.py
```

Streamable HTTP MCP endpoint: `http://localhost:8080/mcp`.

## Tests

```bash
python -m unittest discover -s tests -v
```

Unit tests use a fake model; they **do not** verify Gemini connectivity. A live end-to-end test is required before deployment acceptance.

## Cloud Run

From this repository with Google Cloud CLI authenticated and correct project selected:

```bash
gcloud run deploy hercules-langchain --source . --region us-central1 \
  --no-allow-unauthenticated \
  --set-secrets GOOGLE_API_KEY=hercules-gemini-api-key:latest
```

First create the Secret Manager secret `hercules-gemini-api-key` with the actual key and grant the Cloud Run runtime service account access to that secret. Configure Cloud Run IAM access for the intended MCP client; **ChatGPT's MCP connector must be able to authenticate to the service**. Do not make the endpoint public without an explicit access-control decision.

A live ChatGPT MCP connection is not configured by this repository alone. Confirm that your ChatGPT MCP client supports the selected Cloud Run authentication mechanism. Deployment command is an example, not evidence of deployment.

## Runtime settings

`GOOGLE_API_KEY` (required), `GEMINI_MODEL` (default `gemini-2.5-flash`), `MODEL_TIMEOUT_SECONDS` (default `60`), `PORT` (Cloud Run injects `8080`), `LOG_LEVEL` (default `INFO`).

**Status:** Source implementation, not yet live verified against Gemini, Cloud Run or ChatGPT. Mercury implementation and technical validation gates remain pending.
