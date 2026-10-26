# Telephony Service

Each telephony provider is an isolated package with its own API. `main.py` (project root) is the
only place that knows about all of them: it creates the app and registers each provider's router.

```
telephony-service/
├── main.py                 # app + router registration + X-API-Key guard
├── twilio_provider/        # self-contained: config, schemas, services, client, api, tests
└── telnyx_provider/        # (later) same internal layout
```
Folders are named `*_provider` on purpose: a local package called `twilio` would shadow the Twilio SDK.

## Layers (inside a provider)
`api/` (HTTP only) -> `services/` (logic) -> `clients/` (the only code touching the vendor SDK).
`schemas/` = request/response models, `core/` = errors + phone helpers, `config.py` = env settings.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in your Twilio values
uvicorn main:app --reload --port 8080
pytest                          # 19 tests, no network or Twilio account needed
```
Interactive docs: http://localhost:8080/docs

## First API
```bash
curl -X POST http://localhost:8080/twilio/calls \
  -H "Content-Type: application/json" -H "X-API-Key: change-me" \
  -d '{"to_number": "+919876543210", "message": "Hello, this is a test call."}'
```
`202` + `call_sid` means Twilio accepted the call. The phone rings shortly after.

| Status | Meaning |
|---|---|
| 202 | Call created |
| 401 | Missing/wrong `X-API-Key` (only enforced when `SERVICE_API_KEY` is set) |
| 422 | Bad input, or Twilio rejected it (response includes `twilio_code` + `hint`) |
| 429 | Twilio rate limit |
| 502 | Twilio auth/config problem, outage or network error |
| 503 | `TWILIO_*` settings missing (response lists which) |

## Twilio account setup for the first test
1. Create a Twilio account; copy Account SID + Auth Token into `.env`.
2. Get a Twilio voice number -> `TWILIO_FROM_NUMBER`.
3. **Trial accounts can only call verified numbers**: verify your own phone in the console first (error 21219 otherwise).
4. Enable the destination country under Voice -> Geo permissions (error 21215 otherwise, e.g. India).
5. No public URL/tunnel is needed yet: this API only places the call and speaks a message.

## Not built yet (next steps)
Call status webhook + signature check, call store, hangup/status endpoints, TwiML `<Connect><Stream>`
to the AI layer, pre-call compliance policy (DND/consent), idempotency, rate limiting, `telnyx_provider/`.
