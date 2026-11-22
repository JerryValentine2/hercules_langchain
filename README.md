# Hercules LangChain — v1 MVP

**Default path:** ChatGPT MCP → Cloud Run → Python LangChain → Gemini through Vertex AI using Google Cloud Application Default Credentials (Cloud Run service account). **No separate Gemini API key is needed.** Cloud Run must have an appropriate project, Vertex AI enabled, an authorized service account, and model access.

**Optional path:** `path="external"` uses an OpenAI-compatible endpoint configured via environment variables. It is included but live external-provider testing is deferred.

## MCP tool

`run_langchain(message: str, product_id: str | None = None, path: str | None = None)`

No `path` or `path="gemini"` uses Gemini. `path="external"` uses the configured external endpoint. Unsupported path fails explicitly. Success: `{"status":"success","model":"...","answer":"..."}`; failure: `{"status":"error","error":"..."}`.

## Configuration

Non-secret defaults in `config.yaml`. Deployment-specific overrides: `GEMINI_MODEL`, `GOOGLE_CLOUD_LOCATION`, `GOOGLE_CLOUD_PROJECT`, `EXTERNAL_MODEL`, `EXTERNAL_BASE_URL`. External credentials: `EXTERNAL_API_KEY` from Secret Manager or another approved secret source. Never put secrets in YAML. `PORT` is injected by Cloud Run.

## Local tests

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Unit tests use fake providers; a passing CI run is **not** a live Gemini/Vertex AI test.

## Local run

Authenticate Google Cloud ADC with an authorized identity, choose a project with Vertex AI enabled and Gemini model access:

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
python app.py
```

MCP Streamable HTTP endpoint: `http://localhost:8080/mcp`.

## Deployment from your computer

Download GitHub repository ZIP, extract, then from the extracted folder run:

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com
gcloud run deploy hercules-langchain --source . --region us-central1 --no-allow-unauthenticated
```

The Cloud Run runtime service account needs `roles/aiplatform.user` (or an appropriate narrower role) for Vertex AI and the configured model must be available to the project/region. Authenticate the ChatGPT MCP client to Cloud Run using a supported mechanism. Do not make the service public solely to bypass authentication.

**Deployment is not complete until** a real ChatGPT → MCP → Cloud Run → Gemini → ChatGPT request succeeds. External path is implemented but not live-tested.
