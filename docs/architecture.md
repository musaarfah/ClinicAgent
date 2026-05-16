# ClinicAgent Architecture

ClinicAgent is a small local AI scheduling assistant. It keeps the useful shape of a production virtual-agent system while removing channel, cloud, database, and vendor complexity.

## Runtime Flow

```text
HTTP client
  -> FastAPI /api/chat
  -> AgentOrchestrator
  -> in-memory session history
  -> OpenAI tool calling, Gemini text generation, or fake provider
  -> MCP tool client
  -> MCP scheduling tool server
  -> Postgres-backed scheduling data
  -> response with tool trace
```

## Components

- `api`: FastAPI routes and request/response schemas.
- `agent`: orchestration logic and skill-to-tool mapping.
- `llm`: provider abstraction for OpenAI, Gemini, and deterministic tests.
- `memory`: in-memory conversation storage keyed by session ID.
- `db`: SQLAlchemy models, repository, persisted agent session state, migrations, and seed data.
- `tools`: MCP client adapter used by FastAPI to call scheduling tools.
- `clinic_agent_mcp`: FastMCP server exposing scheduling, appointment, location, and handoff tools.
- `prompts`: system prompt construction.

## OpenAI Tool Calling Flow

```text
User message
  -> orchestrator builds messages and tool schemas
  -> OpenAI chooses zero or more function tools
  -> orchestrator validates enabled tools and calls the MCP server
  -> tool outputs are sent back to OpenAI
  -> OpenAI returns the final user-facing response
```

The backend always owns tool execution. The model can request tools, but it never directly mutates state or calls external services. The MCP server is the only runtime path that reads or writes scheduling state.

## MCP Tool Boundary

```text
FastAPI process
  -> McpToolClient
  -> http://127.0.0.1:9100/mcp
  -> clinic_agent_mcp.server
  -> domain tool modules
  -> SQLAlchemy repositories
  -> Postgres
```

The agent strips `session_id` from schemas shown to OpenAI and injects it when executing MCP calls. That keeps the model focused on user intent while the backend preserves session isolation.

MCP tools are organized by domain under `clinic_agent_mcp/tools`: patients, slots, appointments, locations, handoff, and shared reference resolution. The server module only registers tools and delegates to those modules.

## Session-Aware Booking

When `get_available_slots` runs, the returned slots are stored in Postgres session state. If a later turn asks to book "the first one" or "the second one," the MCP tool server resolves that reference to the previously returned slot before booking.

## Patient Validation

Booking, appointment lookup, and patient-scoped cancellation require a validated patient in the active session. The `validate_patient` tool checks fictional Postgres data by full first and last name plus date of birth, accepts natural DOB formats, and can use phone number only as a fallback after name + DOB do not match. If appointment management is requested before validation, the backend returns `validation_required` and the assistant asks for those details.

## Appointment Lifecycle

The core lifecycle is now:

```text
validate_patient
  -> get_available_slots
  -> book_appointment
  -> get_patient_appointments
  -> cancel_patient_appointment
```

Cancellation is patient-scoped. The MCP server reads the validated patient ID from session state and refuses to cancel appointments that do not belong to that patient.

## Location And Handoff Data

Clinic location details are seeded into Postgres and read through the repository instead of being hardcoded in tool code. Human handoff requests are also persisted as fictional `handoff_requests` rows, which keeps the demo safe while making the workflow production-shaped.

## V1 Simplifications

- REST only; websocket streaming is deferred.
- Chat history remains in-memory; scheduling data and agent tool/session state are persisted.
- Fictional scheduling data only; no real EHR/vendor integration.
- No Twilio, cloud deployment, queues, internal auth, or Redis.
- No production names, secrets, customer data, or internal configs.
- Gemini native tool calling is deferred.

## Future Improvements

- Websocket streaming.
- Persistent chat/session history.
- Native Gemini tool calling.
- More realistic scheduling workflows.
- Lightweight auth for demos.
