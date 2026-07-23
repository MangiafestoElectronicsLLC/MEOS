# Community Validation Endpoint Hardening

This endpoint adds anti-poisoning controls for shared validation votes:
- Required API key authentication
- Optional HMAC request signatures
- Per-IP rate limiting (enabled by default)

## Deploy (Cloudflare Workers)

1. Create a Worker and paste the content from [scripts/community-validation-worker.js](scripts/community-validation-worker.js).
2. Optional but recommended: bind KV namespace as MEOS_VALIDATION_KV for persistent storage.
3. Set environment variables:
- API_KEY: shared token for client requests (required)
- REQUIRE_SIGNATURE: true or false (set to false for simple setup)
- SIGNING_SECRET: HMAC secret used by clients and server
- SIG_MAX_SKEW_SECONDS: allowed clock skew for signatures (default 120)
- RATE_LIMIT_ENABLED: true or false (set to true)
- RATE_LIMIT_WINDOW_SECONDS: window duration (default 60)
- RATE_LIMIT_MAX_REQUESTS: max requests/IP/window (default 60)

You can start from [scripts/community-validation-worker.env.example](scripts/community-validation-worker.env.example).

### Non-Technical Simple Mode

If setup feels too complex, you can run a simpler mode:
- Keep API_KEY set.
- Set REQUIRE_SIGNATURE=false.
- Keep rate limiting enabled.

Then users only need API URL + API key in MEOS Quick Setup.

This is now the default in the example env file.

## Signature format (v1)

Clients sign this canonical string with HMAC-SHA256 hex:

timestamp\nMETHOD\nPATH\nQUERY\nSHA256(body)

Headers expected when signature is enabled:
- X-MEOS-Timestamp
- X-MEOS-Signature
- X-MEOS-Signature-Version: v1

The updated addon client sends these headers when both API key and signature secret are configured.

## Endpoint contract

1. GET /validation?key=<stream-key>
- Returns vote and validated state.

2. POST /validation
- Body:
  - key
  - vote (up/down)
  - source
  - addon
  - version
  - timestamp

## Security notes

- API_KEY is mandatory; missing or invalid keys are rejected.
- With REQUIRE_SIGNATURE=true, unsigned and invalidly signed requests are rejected.
- Rate limiting returns HTTP 429 with retry-after.
- Use HTTPS only.
- Rotate API_KEY and SIGNING_SECRET periodically.
