# ClinicAgent

ClinicAgent is a local AI clinic scheduling assistant. It demonstrates agenitc architecture in a smaller, runnable FastAPI application.


## Features

- FastAPI REST chat endpoint.
- OpenAI provider-driven tool calling, plus Gemini and fake provider options.
- MCP-based scheduling tools organized by domain with skill-based tool access.
- Postgres-backed fictional patients, slots, booking, cancellation, locations, and human handoff.
- In-memory chat history and Postgres-backed agent session state for references like "book the second one."
- Pytest coverage for API, memory, tools, and orchestration.

## Setup

```bash
cd ~/Desktop/ClinicAgent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Start the local Postgres database and seed fictional data:

```bash
docker compose up -d postgres
alembic upgrade head
python -m clinic_agent.db.seed
```

Start the MCP tool server in a second terminal:

```bash
source .venv/bin/activate
python -m clinic_agent_mcp.server
```

For local deterministic behavior, keep:

```bash
LLM_PROVIDER=fake
```

For OpenAI:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
MCP_SERVER_URL=http://127.0.0.1:9100/mcp
```

OpenAI mode lets the model choose which tools to call. FastAPI sends the selected tool call to the MCP server, sends the MCP output back to OpenAI, and returns the final assistant response.

For Gemini:

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-1.5-flash
```

## Run

In another terminal:

```bash
uvicorn clinic_agent.main:app --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## Run The Chat UI

In a second terminal:

```bash
cd ~/Desktop/ClinicAgent/client
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The UI stores the active `session_id` automatically and shows tool activity in expandable debug panels.

## Current Demo Workflows

- Find available appointment slots.
- Validate a fictional patient with full first and last name plus DOB.
- Book a selected slot after validation.
- View appointments for the validated patient.
- Cancel a selected appointment and make its slot available again.
- Ask for clinic location details or request a human handoff.
- Start a new isolated chat session from the UI.

## Example API Calls

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Can you find available appointment slots?"}'
```

Continue a session:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION_ID","message":"Please book one"}'
```

Inspect session memory:

```bash
curl http://127.0.0.1:8000/api/sessions/SESSION_ID
```

Create a fresh backend session with the assistant greeting:

```bash
curl -X POST http://127.0.0.1:8000/api/sessions
```

Validate a patient before booking:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION_ID","message":"My name is Jamie Rivera DOB 1990-01-01"}'
```

## Test

```bash
pytest
```

The tests use an in-process MCP tool client so they do not require a running MCP server.

