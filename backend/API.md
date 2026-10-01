# API.md — HGW Dashboard API Reference

> Base URL (dev): `http://localhost:8000`  
> Base URL (Docker): `http://localhost:8000` (proxied through nginx at `/api/`)  
> Interactive docs: `http://localhost:8000/docs`  
> All authenticated endpoints require header: `Authorization: Bearer <JWT>`

---

## Authentication

### POST `/auth/login`
Login and receive a JWT token.

**Body:**
```json
{ "username": "admin", "password": "yourpassword" }
```
**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "Admin User",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true
  }
}
```
**Errors:** `401 Invalid username or password`

---

### POST `/auth/logout`
Auth required. Marks the current session as ended.

**Response 200:** `{ "message": "Déconnecté" }`

---

### GET `/auth/me`
Auth required. Returns the current user profile decoded from JWT.

**Response 200:** UserOut object (same as login user field)

---

### POST `/auth/verify`
Auth required. Validates that the token is still valid.

**Response 200:** `{ "valid": true, "user": { ... } }`

---

### POST `/auth/change-password`
Auth required. Change the current user's password.

**Body:**
```json
{ "current_password": "old", "new_password": "newmin8chars" }
```
**Response 200:** `{ "message": "Password updated successfully" }`  
**Errors:** `400` (too short), `401` (wrong current password)

---

## User Management (Admin only)

### GET `/auth/users`
Returns all users.

**Response 200:**
```json
[
  { "id": 1, "username": "admin", "full_name": "...", "role": "admin", "is_active": true, "created_at": "..." }
]
```

### POST `/auth/users`
Create a new user.

**Body:**
```json
{
  "username": "john",
  "password": "securepass",
  "full_name": "John Doe",
  "email": "john@example.com",
  "role": "general"
}
```
Roles: `"admin"` | `"engineer"` | `"general"`

**Response 200:** `{ "message": "Utilisateur créé avec succès" }`

### DELETE `/auth/users/{user_id}`
Delete a user. Admin only.

### PATCH `/auth/users/{user_id}/toggle?active=true`
Activate or deactivate a user account.

---

## Chat (Main Endpoint)

### POST `/chat-voice/`
**Auth required.** The primary AI chat endpoint. Accepts a user message, runs the LLM pipeline with MCP tools, and returns a text response plus optional audio.

**Body:**
```json
{
  "message": "What is the WiFi status?",
  "history": [
    { "role": "user", "content": "previous question" },
    { "role": "assistant", "content": "previous answer" }
  ],
  "gateway_id": 1,
  "with_voice": true,
  "language_code": "fr",
  "is_voice_input": false
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `message` | string | required | User's question |
| `history` | array | `[]` | Last N messages for context (send max 4) |
| `gateway_id` | int \| null | null | Target gateway (uses its Telnet credentials) |
| `with_voice` | bool | true | Generate audio response |
| `language_code` | string | `"fr"` | TTS language (`"fr"`, `"en"`, `"ar"`, …) |
| `is_voice_input` | bool | false | True when message came from microphone |

**Response 200:**
```json
{
  "response": "The WiFi is currently enabled. SSID: Livebox-5G on channel 100.",
  "tool_calls_count": 1,
  "audio_base64": "//NExAA...",
  "voice_available": true,
  "log_id": 42
}
```

| Field | Description |
|---|---|
| `response` | LLM-generated text answer |
| `tool_calls_count` | Number of MCP tools invoked |
| `audio_base64` | MP3 audio encoded in base64 (null if TTS failed or with_voice=false) |
| `voice_available` | Whether audio was successfully generated |
| `log_id` | ID of the saved chat_log row (used for feedback) |

**Errors:**
- `504` — LLM or gateway timed out (>3 minutes)
- `500` — Unexpected error (see `detail`)

**Context meta-commands** (no tools called, uses previous answer):

| Say | Effect |
|---|---|
| "go deeper", "more detail", "elaborate" | Deeper technical analysis of last response |
| "simpler", "in simple terms" | Plain-English rewrite |
| "explain again", "repeat", "clarify" | Rephrase at same depth |
| "summarize", "tldr", "briefly" | 1-2 sentence summary |

---

## Voice (STT / TTS)

### POST `/voice/stt`
Speech-to-text. Requires Google Cloud credentials (`GOOGLE_APPLICATION_CREDENTIALS`).

**Body:** `multipart/form-data`
- `audio` — audio file (WebM/OGG from MediaRecorder)
- `language_code` — optional, default `"fr-FR"`

**Response 200:**
```json
{ "text": "Quel est le statut du WiFi ?", "confidence": 0.97, "language": "fr-FR" }
```
**Error 503:** Google Cloud libraries not configured

---

### POST `/voice/tts`
Text-to-speech via Google Cloud Neural TTS.

**Body:**
```json
{ "text": "Hello", "language_code": "fr-FR", "voice_name": "fr-FR-Neural2-A" }
```
**Response 200:**
```json
{ "audio_base64": "//NExAA...", "duration_seconds": 1.4 }
```

---

### GET `/voice/status`
Check voice service availability.

**Response 200:**
```json
{ "status": "available", "stt": "ready", "tts": "ready" }
```

---

## Chat Logs (Admin only)

### GET `/chat-logs`
List chat logs with optional filters.

**Query params:**

| Param | Type | Description |
|---|---|---|
| `user_id` | int | Filter by user |
| `gateway_id` | int | Filter by gateway |
| `date_from` | string | `YYYY-MM-DD` start date |
| `date_to` | string | `YYYY-MM-DD` end date |
| `limit` | int | Max results (1–2000, default 100) |
| `offset` | int | Pagination offset |

**Response 200:** Array of ChatLog objects
```json
[{
  "id": 42,
  "user_id": 1,
  "username": "engineer1",
  "session_id": 5,
  "gateway_id": 1,
  "gateway_name": "Home Router",
  "message": "WiFi status?",
  "response": "WiFi is enabled...",
  "tool_calls": 1,
  "voice_used": 0,
  "duration_ms": 3200,
  "user_type": "engineer",
  "feedback": null,
  "created_at": "2026-05-20T10:30:00"
}]
```

---

### GET `/chat-logs/stats`
Aggregate statistics across all logs.

**Response 200:**
```json
{
  "total_interactions": 1250,
  "active_users_count": 5,
  "by_user": [{ "username": "admin", "cnt": 300 }],
  "by_gateway": [{ "gateway": "Home Router", "cnt": 800 }],
  "last_7_days": [{ "day": "2026-05-20", "cnt": 45 }],
  "voice_usage": { "voice_count": 120, "text_count": 1130 }
}
```

---

### GET `/chat-logs/{log_id}`
Get a single log entry.

### DELETE `/chat-logs/{log_id}`
Delete a log entry.

---

### POST `/chat-logs/compare`
Replay a message with both `general` and `engineer` roles and return both responses.

**Body:**
```json
{ "message": "What is the WiFi status?", "gateway_id": 1 }
```
**Response 200:**
```json
{
  "general": "WiFi is on. Network: Livebox-5G.",
  "technical": "The WiFi radio is active on both 2.4 GHz (channel 6, WPA2) and 5 GHz (channel 100, WPA2-WPA3-Personal). SSID: Livebox-5G...",
  "general_tools": 1,
  "technical_tools": 1
}
```

---

### POST `/chat-logs/{log_id}/correct`
Save an admin correction for a log entry (stored as evaluation data).

**Body:**
```json
{ "corrected_response": "The corrected, more accurate answer." }
```
**Response 200:** `{ "message": "Correction saved", "log_id": 42 }`

---

### GET `/chat-logs/{log_id}/correction`
Get the admin correction for a log entry, or 404 if none.

---

### POST `/chat-logs/{log_id}/feedback`
Auth required (any role). Submit thumbs up/down.

**Body:**
```json
{ "value": "up" }
```
Values: `"up"` | `"down"`

---

## Admin Statistics

All endpoints require `admin` role.

### GET `/admin/stats/kpi`
Main KPI dashboard numbers.

**Response 200:**
```json
{
  "total_messages": 1250,
  "voice_messages": 120,
  "text_messages": 1130,
  "active_users_24h": 3,
  "gateways_count": 4,
  "voice_percentage": 9.6
}
```

### GET `/admin/stats/activity`
Message count per day for the last 7 days.

**Response 200:**
```json
{
  "2026-05-14": { "count": 45, "voice": 5 },
  "2026-05-15": { "count": 62, "voice": 8 }
}
```

### GET `/admin/stats/voice-text`
Voice vs text split.

**Response 200:** `{ "text": 1130, "voice": 120 }`

### GET `/admin/stats/top-users?limit=5`
Top N users by message count.

### GET `/admin/stats/recent-messages?limit=20`
Most recent messages with full detail.

### GET `/admin/stats/top-questions?limit=10`
Most frequently asked questions (exact match).

### GET `/admin/stats/feedback`
Feedback statistics.

**Response 200:**
```json
{
  "up_count": 85,
  "down_count": 12,
  "total_rated": 97,
  "total": 1250,
  "positive_rate": 87.6,
  "rated_rate": 7.8
}
```

### GET `/admin/stats/response-time`
Average/min/max response times overall and by user type.

**Response 200:**
```json
{
  "overall": { "avg_ms": 4200, "min_ms": 800, "max_ms": 28000 },
  "by_type": [
    { "user_type": "engineer", "avg_ms": 6500, "cnt": 400 },
    { "user_type": "general", "avg_ms": 2800, "cnt": 850 }
  ]
}
```

### GET `/admin/stats/hourly`
Message count by hour of day (0-23).

**Response 200:** `{ "0": 2, "1": 0, ..., "14": 120, "15": 98, ... }`

---

## Prompt Management (Admin only)

### GET `/prompts`
Get the current merged prompt configuration (YAML overrides + hardcoded defaults).

**Response 200:**
```json
{
  "general":   { "system": "You are an HGW assistant...", "max_tokens": 300 },
  "technical": { "system": "You are an HGW engineer assistant...", "max_tokens": 700 },
  "context_commands": { "max_tokens": 700 }
}
```

### PUT `/prompts`
Update prompt configuration and hot-reload (no server restart needed).

**Body:**
```json
{
  "general":   { "system": "New system prompt...", "max_tokens": 400 },
  "technical": { "system": "New technical prompt..." }
}
```

### POST `/prompts/reload`
Hot-reload `prompts.yaml` from disk.

---

## Gateway Management

### GET `/gateways`
Auth required. Returns all gateways (admin sees all, other roles see their own).

**Response 200:**
```json
[{
  "id": 1,
  "name": "Home Router",
  "ipv4_address": "192.168.2.254",
  "telnet_host": "192.168.2.254",
  "telnet_port": 23,
  "created_at": "2026-04-01T10:00:00"
}]
```

### GET `/gateways/{id}`
Get a single gateway by ID.

### POST `/gateways`
Engineer or admin. Create a new gateway entry.

**Body:**
```json
{
  "name": "Office Router",
  "ipv4_address": "192.168.1.1",
  "telnet_host": "192.168.1.1",
  "telnet_port": 23,
  "telnet_user": "root",
  "telnet_password": "sah"
}
```

### PUT `/gateways/{id}`
Update a gateway entry.

### DELETE `/gateways/{id}`
Admin only. Delete a gateway.

### GET `/gateways/{id}/ping`
TCP ping (port 23) to check gateway reachability and measure latency.

**Response 200:**
```json
{ "status": "reachable", "latency_ms": 12.5, "host": "192.168.2.254" }
```
Status values: `"reachable"` | `"timeout"` | `"unreachable"`

---

## HGW Control Endpoints

These endpoints send Telnet commands to the physical gateway. All require auth.

### WiFi

| Method | Endpoint | Description |
|---|---|---|
| POST | `/wifi/on` | Enable WiFi (2.4 + 5 GHz) |
| POST | `/wifi/off` | Disable WiFi |
| POST | `/wifi/status` | Full WiFi status |
| POST | `/wifi/ssid` | Change SSID (body: `{ssid: "MyNet", ...telnet_config}`) |
| POST | `/wifi/password` | Change password (body: `{keypassphrase: "...", ...}`) |
| POST | `/wifi/get-password` | Get current password |
| POST | `/wifi/reboot` | Reboot gateway |
| POST | `/wifi/factory-reset` | Factory reset WiFi settings |
| POST | `/wifi/speedtest` | Run internet speed test |
| POST | `/wifi/extra-2g/on` | Enable 2.4 GHz extra radio |
| POST | `/wifi/extra-2g/off` | Disable 2.4 GHz extra radio |
| POST | `/wifi/extra-5g/on` | Enable 5 GHz extra radio |
| POST | `/wifi/extra-5g/off` | Disable 5 GHz extra radio |

### Guest WiFi

| Method | Endpoint | Description |
|---|---|---|
| POST | `/guestwifi/2g/on` | Enable guest 2.4 GHz |
| POST | `/guestwifi/2g/off` | Disable guest 2.4 GHz |
| POST | `/guestwifi/5g/on` | Enable guest 5 GHz |
| POST | `/guestwifi/5g/off` | Disable guest 5 GHz |
| POST | `/guestwifi/status` | Guest WiFi status |
| POST | `/guestwifi/ssid` | Change guest SSID |
| POST | `/guestwifi/password` | Change guest password |

### Firewall

| Method | Endpoint | Description |
|---|---|---|
| POST | `/firewall/respond-to-ping/enable` | Allow ping responses |
| POST | `/firewall/respond-to-ping/disable` | Block ping responses |
| POST | `/firewall/level?level=Medium` | Set level: `Low` / `Medium` / `High` |
| POST | `/firewall/firewall/status?role=normal` | Status (normal or technical) |

### Other Services

| Endpoint | Description |
|---|---|
| `POST /dhcp/status?role=normal` | DHCP server status |
| `POST /wan/status?role=normal` | WAN connection status |
| `POST /voip/status?role=normal` | VoIP service status |
| `POST /IPTV/status?role=normal` | IPTV service status |
| `POST /devices/devices/list?role=normal` | Connected devices list |
| `POST /devices/devices/hgw` | HGW hardware info |
| `POST /debogageavance/faults` | List gateway faults |
| `POST /debogageavance/oopses` | List kernel crashes |
| `POST /debogageavance/verify-plugins` | Verify all plugins |
| `POST /debogageavance/mqtt` | MQTT broker status |
| `POST /debogageavance/devices/modem/status?role=normal` | Modem status |
| `POST /debogageavance/Access?role=normal` | Network access diagnostic |
| `POST /telnet/execute` | Raw Telnet commands (body: `{commands: ["NMC.Wifi.get()"]}`) |
| `POST /scheduler/add` | Add WLAN schedule |
| `POST /scheduler/enable` | Enable a schedule |
| `POST /scheduler/disable` | Disable a schedule |

All HGW control endpoints accept a body with Telnet connection info:
```json
{
  "host": "192.168.2.254",
  "port": 23,
  "user": "root",
  "password": "sah"
}
```
If omitted, the server uses the gateway configuration from the database.

---

## Error Codes

| Code | Meaning |
|---|---|
| 400 | Bad request / validation error |
| 401 | Missing or invalid JWT |
| 403 | Insufficient role (admin required) |
| 404 | Resource not found |
| 422 | Pydantic validation error (check request body) |
| 500 | Internal server error |
| 503 | Voice service unavailable (Google Cloud not configured) |
| 504 | Gateway timeout (LLM or HGW did not respond in time) |
