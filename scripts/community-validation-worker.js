// MEOS Community Validation Endpoint (Cloudflare Worker style)
// Features:
// - GET /validation?key=<stream-key>
// - POST /validation { key, vote, source, addon, version, timestamp }
// - Optional API key auth
// - Optional HMAC signature validation
// - Optional in-memory per-IP rate limiting
//
// Environment variables:
// - API_KEY (required)
// - REQUIRE_SIGNATURE ("true"/"false", default "false")
// - SIGNING_SECRET (required if REQUIRE_SIGNATURE=true)
// - SIG_MAX_SKEW_SECONDS (default "120")
// - RATE_LIMIT_ENABLED ("true"/"false", default "true")
// - RATE_LIMIT_WINDOW_SECONDS (default "60")
// - RATE_LIMIT_MAX_REQUESTS (default "60")
//
// Optional KV binding:
// - MEOS_VALIDATION_KV

const memoryStore = new Map();
const rateLimitStore = new Map();

function jsonResponse(payload, status = 200, extraHeaders = {}) {
    return new Response(JSON.stringify(payload), {
        status,
        headers: {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "no-store",
            ...extraHeaders,
        },
    });
}

function parseBool(value, fallback = false) {
    if (value === undefined || value === null || value === "") {
        return fallback;
    }
    return ["1", "true", "yes", "on"].includes(String(value).toLowerCase());
}

function ipFromRequest(request) {
    return (
        request.headers.get("CF-Connecting-IP") ||
        request.headers.get("X-Forwarded-For") ||
        request.headers.get("X-Real-IP") ||
        "unknown"
    )
        .split(",")[0]
        .trim();
}

function normalizedVote(vote) {
    const value = String(vote || "").trim().toLowerCase();
    if (["up", "working", "validated", "ok", "true", "1"].includes(value)) {
        return "up";
    }
    if (["down", "nonworking", "non-working", "fail", "false", "0"].includes(value)) {
        return "down";
    }
    return "";
}

async function applyRateLimit(request, env) {
    const enabled = parseBool(env.RATE_LIMIT_ENABLED, true);
    if (!enabled) {
        return null;
    }

    const now = Date.now();
    const windowSeconds = Math.max(parseInt(env.RATE_LIMIT_WINDOW_SECONDS || "60", 10) || 60, 1);
    const maxRequests = Math.max(parseInt(env.RATE_LIMIT_MAX_REQUESTS || "60", 10) || 60, 1);
    const windowMs = windowSeconds * 1000;

    const ip = ipFromRequest(request);
    const key = `${ip}:${new URL(request.url).pathname}`;
    const current = rateLimitStore.get(key);

    if (!current || current.resetAt <= now) {
        rateLimitStore.set(key, { count: 1, resetAt: now + windowMs });
        return null;
    }

    current.count += 1;
    rateLimitStore.set(key, current);

    if (current.count > maxRequests) {
        const retryAfter = Math.max(Math.ceil((current.resetAt - now) / 1000), 1);
        return jsonResponse(
            {
                ok: false,
                error: "rate_limited",
                retryAfter,
            },
            429,
            {
                "retry-after": String(retryAfter),
            }
        );
    }

    return null;
}

function verifyApiKey(request, env) {
    const expected = String(env.API_KEY || "").trim();
    if (!expected) {
        return false;
    }

    const provided =
        request.headers.get("X-API-Key") ||
        (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");

    return String(provided || "").trim() === expected;
}

function toHex(buffer) {
    return Array.from(new Uint8Array(buffer))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
}

async function sha256Hex(text) {
    const bytes = new TextEncoder().encode(text || "");
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return toHex(digest);
}

async function hmacHex(secret, text) {
    const key = await crypto.subtle.importKey(
        "raw",
        new TextEncoder().encode(secret),
        { name: "HMAC", hash: "SHA-256" },
        false,
        ["sign"]
    );
    const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(text));
    return toHex(signature);
}

async function verifySignature(request, env, bodyText) {
    const required = parseBool(env.REQUIRE_SIGNATURE, false);
    if (!required) {
        return { ok: true };
    }

    const secret = String(env.SIGNING_SECRET || "").trim();
    if (!secret) {
        return { ok: false, error: "signature_secret_not_configured" };
    }

    const timestamp = String(request.headers.get("X-MEOS-Timestamp") || "").trim();
    const signature = String(request.headers.get("X-MEOS-Signature") || "").trim().toLowerCase();

    if (!timestamp || !signature) {
        return { ok: false, error: "missing_signature_headers" };
    }

    const tsInt = parseInt(timestamp, 10);
    if (!Number.isFinite(tsInt)) {
        return { ok: false, error: "invalid_timestamp" };
    }

    const skewMax = Math.max(parseInt(env.SIG_MAX_SKEW_SECONDS || "120", 10) || 120, 10);
    const now = Math.floor(Date.now() / 1000);
    if (Math.abs(now - tsInt) > skewMax) {
        return { ok: false, error: "timestamp_out_of_window" };
    }

    const url = new URL(request.url);
    const bodyHash = await sha256Hex(bodyText || "");
    const canonical = [timestamp, request.method.toUpperCase(), url.pathname || "/", url.search.replace(/^\?/, ""), bodyHash].join("\n");
    const expected = await hmacHex(secret, canonical);

    if (expected !== signature) {
        return { ok: false, error: "invalid_signature" };
    }

    return { ok: true };
}

async function kvGet(env, key) {
    if (env.MEOS_VALIDATION_KV) {
        const raw = await env.MEOS_VALIDATION_KV.get(key);
        return raw ? JSON.parse(raw) : null;
    }
    return memoryStore.get(key) || null;
}

async function kvSet(env, key, value) {
    if (env.MEOS_VALIDATION_KV) {
        await env.MEOS_VALIDATION_KV.put(key, JSON.stringify(value));
        return;
    }
    memoryStore.set(key, value);
}

function sanitizeKey(value) {
    const key = String(value || "").trim();
    if (!key || key.length > 1024) {
        return "";
    }
    return key;
}

export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        if (url.pathname !== "/validation") {
            return jsonResponse({ ok: false, error: "not_found" }, 404);
        }

        const limited = await applyRateLimit(request, env);
        if (limited) {
            return limited;
        }

        if (!verifyApiKey(request, env)) {
            return jsonResponse({ ok: false, error: "unauthorized" }, 401);
        }

        let bodyText = "";
        if (request.method === "POST") {
            bodyText = await request.text();
        }

        const signatureResult = await verifySignature(request, env, bodyText);
        if (!signatureResult.ok) {
            return jsonResponse({ ok: false, error: signatureResult.error }, 401);
        }

        if (request.method === "GET") {
            const key = sanitizeKey(url.searchParams.get("key"));
            if (!key) {
                return jsonResponse({ ok: false, error: "missing_key" }, 400);
            }

            const record = await kvGet(env, key);
            if (!record) {
                return jsonResponse({ ok: true, key, vote: "", validated: false });
            }

            return jsonResponse({
                ok: true,
                key,
                vote: normalizedVote(record.vote),
                validated: normalizedVote(record.vote) === "up",
                updatedAt: record.updatedAt || 0,
                source: record.source || "unknown",
            });
        }

        if (request.method === "POST") {
            let payload;
            try {
                payload = bodyText ? JSON.parse(bodyText) : {};
            } catch (_err) {
                return jsonResponse({ ok: false, error: "invalid_json" }, 400);
            }

            const key = sanitizeKey(payload.key);
            const vote = normalizedVote(payload.vote);
            const source = String(payload.source || "unknown").slice(0, 64);
            const addon = String(payload.addon || "").slice(0, 128);
            const version = String(payload.version || "").slice(0, 64);

            if (!key) {
                return jsonResponse({ ok: false, error: "missing_key" }, 400);
            }
            if (!vote) {
                return jsonResponse({ ok: false, error: "invalid_vote" }, 400);
            }

            const record = {
                vote,
                source,
                addon,
                version,
                timestamp: Number(payload.timestamp || 0),
                updatedAt: Date.now(),
            };

            await kvSet(env, key, record);
            return jsonResponse({ ok: true, key, vote, validated: vote === "up", updatedAt: record.updatedAt });
        }

        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405, {
            allow: "GET, POST",
        });
    },
};
