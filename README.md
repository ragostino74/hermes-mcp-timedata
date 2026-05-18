# Hermes MCP Server — TimeData

MCP (Model Context Protocol) server che espone strumenti per data/ora e conversioni temporali.
Permette a qualsiasi client MCP di accedere a informazioni temporali con formattazione italiana.

## Funzionalità

- **get_current_datetime** — Data e ora attuale in italiano (Europe/Rome)
- **get_current_datetime_utc** — Data e ora attuale in UTC
- **get_current_datetime_tz** — Data e ora per un fuso orario IANA specificato
- **timestamp_to_datetime** — Converte Unix timestamp a data/ora leggibile
- **datetime_to_timestamp** — Converte data/ora a Unix timestamp

## Requisiti

- Python 3.11+
- [`mcp[serve]`](https://pypi.org/project/mcp/) >= 1.26

## Installazione

```bash
# Crea un ambiente virtuale
python3 -m venv .venv
source .venv/bin/activate

# Installa le dipendenze
pip install mcp[serve]

# Avvia in modalità stdio (per Claude Desktop, VS Code, ecc.)
python hermes_mcp_timedata.py

# Oppure in modalità HTTP/StreamableHTTP (per llama.cpp WebUI)
export HERMES_MCP_TRANSPORT=http
export HERMES_MCP_PORT=18761
python hermes_mcp_timedata.py
```

## Configurazione Environment Variables

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `HERMES_MCP_TRANSPORT` | `stdio` | Modalità di trasporto: `stdio`, `http`, o `dual` |
| `HERMES_MCP_PORT` | `18761` | Porta per la modalità HTTP/StreamableHTTP |
| `HERMES_MCP_BIND_ADDR` | `127.0.0.1` | Bind IP per il server MCP HTTP (default sicuro: localhost) |
| `HERMES_MCP_CORS_ORIGINS` | `http://localhost:*,https://localhost:*` | CORS origins, comma-separated. Imposta `[]` per same-origin-only |
| `HERMES_MCP_ALLOWED_HOSTS` | `localhost,127.0.0.1,::1` | Hosts consentiti per Host header check (DNS rebinding protection) |

## Integrazione con llama.cpp WebUI

1. Apri la WebUI in browser
2. Vai alla sezione **MCP Servers**
3. Aggiungi un nuovo server con:
   - **URL**: `http://localhost:18761/mcp` (o l'IP della tua macchina)
   - **Transport**: `streamable_http`
4. Il server dovrebbe connettersi e mostrare i 5 tools disponibili

## Integrazione con altri client MCP

Lo script supporta anche la modalità **stdio** per:
- **Claude Desktop** — aggiungi al config JSON
- **VS Code** — estensioni MCP
- Qualsiasi altro client che supporti il protocollo MCP via stdio

## Strumenti Dettagliati

### get_current_datetime

Restituisce data/ora corrente in formato italiano (Europe/Rome).

### get_current_datetime_utc

Restituisce data/ora corrente in UTC.

### get_current_datetime_tz(timezone_name)

Restituisce data/ora corrente per un fuso orario IANA.

Esempio: `America/New_York`, `Asia/Tokyo`, `Europe/London`

### timestamp_to_datetime(unix_timestamp)

Converte un Unix timestamp a data/ora leggibile in italiano (Europe/Rome).

### datetime_to_timestamp(date, time, format)

Converte una data/ora a Unix timestamp. Supporta formati ISO e custom.

## Licenza

MIT License — vedi file [LICENSE](LICENSE).
