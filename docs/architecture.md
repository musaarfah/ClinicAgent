# ClinicAgent Architecture

ClinicAgent is a small local AI scheduling assistant. It keeps the useful shape of a production virtual-agent system while removing channel, cloud, database, and vendor complexity.

## Runtime Flow

```text
HTTP client
  -> FastAPI /api/chat
  -> AgentOrchestrator
  -> in-memory session history
  -> local tool registry
  -> OpenAI tool calling, Gemini text generation, or fake provider
  -> Postgres-backed scheduling data
  -> response with tool trace
```

## Components

- `api`: FastAPI routes and request/response schemas.
- `agent`: orchestration logic and skill-to-tool mapping.
- `llm`: provider abstraction for OpenAI, Gemini, and deterministic tests.
- `memory`: in-memory conversation storage keyed by session ID.
- `db`: SQLAlchemy models, repository, migrations, and seed data.
- `tools`: local scheduling tools backed by fictional Postgres data.
- `prompts`: system prompt construction.

## OpenAI Tool Calling Flow

```text
User message
  -> orchestrator builds messages and tool schemas
  -> OpenAI chooses zero or more function tools
  -> orchestrator validates enabled tools and executes local code
  -> tool outputs are sent back to OpenAI
  -> OpenAI returns the final user-facing response
```

The backend always owns tool execution. The model can request tools, but it never directly mutates state or calls external services.

## Session-Aware Booking

When `get_available_slots` runs, the returned slots are stored in session state. If a later turn asks to book "the first one" or "the second one," the orchestrator resolves that reference to the previously returned slot before running `book_appointment`.

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

Cancellation is patient-scoped. The backend injects the validated patient ID and refuses to cancel appointments that do not belong to that patient.

## V1 Simplifications

- REST only; websocket streaming is deferred.
- Chat/session state remains in-memory; scheduling data is persisted.
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
