# Hermes MCP Server — TimeData

MCP (Model Context Protocol) server che espone strumenti per data/ora e conversioni temporali.

## Funzionalità

- **get_current_datetime** — Data e ora attuale in italiano (Europe/Rome)
- **get_current_datetime_utc** — Data e ora corrente in UTC
- **get_current_datetime_tz(timezone_name)** — Ora per un fuso IANA
- **timestamp_to_datetime(unix_timestamp)** — Converte timestamp a data/ora italiana
- **datetime_to_timestamp(date, time, format)** — Converte data/ora a timestamp

## Requisiti

- Python 3.11+
- [`mcp[serve]`](https://pypi.org/project/mcp/) >= 1.26

## Installazione

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install mcp[serve]
```

## Esecuzione

```bash
# STDIO — per Hermes Agent, Claude Desktop, VS Code
python hermes_mcp_timedata.py

# HTTP/StreamableHTTP — per llama.cpp WebUI e browser
HERMES_MCP_TRANSPORT=http HERMES_MCP_PORT=18761 python hermes_mcp_timedata.py
```

## Variabili d'ambiente

| Variabile | Default | Descrizione |
|---|---|---|
| `HERMES_MCP_TRANSPORT` | `stdio` | Modalità: `stdio`, `http`, o `dual` |
| `HERMES_MCP_PORT` | `18761` | Porta HTTP per StreamableHTTP |
| `HERMES_MCP_BIND_ADDR` | `0.0.0.0` | IP di bind (usa `127.0.0.1` in produzione) |
| `HERMES_MCP_CORS_ORIGINS` | *(vuoto)* | CORS origins, comma-separated. `[]` per same-origin |
| `HERMES_MCP_ALLOWED_HOSTS` | `localhost,127.0.0.1,::1` | Host consentiti (DNS rebinding protection) |

## Integrazione con llama.cpp WebUI

1. Avvia il server in modalità HTTP sulla macchina che ospita i tools:
   ```bash
   HERMES_MCP_TRANSPORT=http HERMES_MCP_PORT=18761 \
     HERMES_MCP_CORS_ORIGINS="*" \
     python hermes_mcp_timedata.py
   ```

2. Nella WebUI di llama.cpp vai su **MCP Servers** → aggiungi:
   - **URL**: `http://<IP_MACCHINA>:18761/mcp`
   - **Transport**: `streamable_http`

Il server gestisce automaticamente l'header `mcp-protocol-version` (non standard MCP) inviato da llama.cpp, e il CORS è configurato per accettare richieste cross-origin dal browser.

## Note sulla sicurezza

- Nessun SSRF (opera solo su datetime locale)
- DNS rebinding protection: disabilitata di default; usa `HERMES_MCP_ALLOWED_HOSTS` se la riattivi
- Bind `0.0.0.0` di default — usa `127.0.0.1` su reti non affidabili
