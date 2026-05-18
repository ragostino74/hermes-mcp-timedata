# Changelog

Tutti i cambiamenti degni di nota in questo progetto saranno documentati in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e questo progetto aderisce a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-18

### Fixed
- **Host header blocking web-gui**: Rimosso `TransportSecuritySettings` che causava "Invalid Host header" quando il client MCP HTTP si connetteva da IP remoti (es. llama.cpp WebUI su `10.0.0.70:18761`). Il server ora funziona correttamente via browser.
- **HTTP bind address**: Bind ora su `0.0.0.0` (era `127.0.0.1`), per permettere connessioni remote dal web-gui.
- **CORS宽松**: `allow_origins=["*"]` e `allow_headers=["*"]` per compatibilità con llama.cpp WebUI.

### Changed
- **Port default**: Cambiata da 18762 a 18761 per coerenza con il servizio systemd installato.

### Added
- **5 strumenti completi**: `get_current_datetime`, `get_current_datetime_utc`, `get_current_datetime_tz`, `timestamp_to_datetime`, `datetime_to_timestamp`.
