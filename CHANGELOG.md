# Changelog

Tutti i cambiamenti degni di nota in questo progetto saranno documentati in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e questo progetto aderisce a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] — 2026-05-21

### Fixed
- **CORS allow_headers**: ristretto da `["*"]` a headers specifici MCP (`Content-Type`, `Authorization`, `Mcp-Session-Id`). Rimossi header non necessari (`Cache-Control`, `Content-Disposition`).
- **CORS expose_headers**: ridotto a solo `Mcp-Session-Id`.
- **Banner/version allineato**: v0.2.3 in docstring, banner print e health endpoint.

### Added
- **Note sulla sicurezza (README)**: sezione documentante SSRF-safe, DNS rebinding, bind localhost, CORS restrittivo.

## [0.2.2] — 2026-05-18

### Fixed
- **DNS rebinding protection riabilitata**: `enable_dns_rebinding_protection=True` (era `False`). Configura `HERMES_MCP_ALLOWED_HOSTS` per aggiungere hosts remoti.
- **CORS configurabile**: Le origini CORS sono ora controllate via `HERMES_MCP_CORS_ORIGINS` (default: `http://localhost:*,https://localhost:*` invece di `*`).
- **Bind address configurabile**: `HERMES_MCP_BIND_ADDR` ora funziona (default: `127.0.0.1` invece di `0.0.0.0`).
- **Dual mode**: Risolto loop ricorsivo infinito — stdio e HTTP ora girano concorrentemente con `asyncio.gather()`.
- **Parametro `format` rinominato**: `format` → `fmt` per evitare shadowing del built-in Python.

### Added
- **Health check endpoint**: `/health` restituisce JSON con stato, versione e configurazione.
- **Logging migliorato**: `log_level="info"` (era `warning`), e stampa config all'avvio.
- **Tipo-safe**: Tipizzazione completa delle funzioni con type hints.

### Changed
- **Default bind addr**: Cambiato da `0.0.0.0` a `127.0.0.1` per sicurezza (solo localhost).

## [0.2.1] — 2026-05-18

### Fixed
- **DNS rebinding protection** (`enable_dns_rebinding_protection=False`): fix "Invalid Host header" / HTTP 421 error when connecting from remote clients (e.g. Hermes Agent WebUI on `10.0.0.70:10000` connecting to MCP server on `10.0.0.70:18761`).

## [0.2.0] — 2026-05-18

### Fixed
- **Host header blocking web-gui**: Rimosso `TransportSecuritySettings` che causava "Invalid Host header" quando il client MCP HTTP si connetteva da IP remoti (es. llama.cpp WebUI su `10.0.0.70:18761`). Il server ora funziona correttamente via browser.
- **HTTP bind address**: Bind ora su `0.0.0.0` (era `127.0.0.1`), per permettere connessioni remote dal web-gui.
- **CORS宽松**: `allow_origins=["*"]` e `allow_headers=["*"]` per compatibilità con llama.cpp WebUI.

### Changed
- **Port default**: Cambiata da 18762 a 18761 per coerenza con il servizio systemd installato.

### Added
- **5 strumenti completi**: `get_current_datetime`, `get_current_datetime_utc`, `get_current_datetime_tz`, `timestamp_to_datetime`, `datetime_to_timestamp`.
