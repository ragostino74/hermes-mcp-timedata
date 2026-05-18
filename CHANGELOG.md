# Changelog

## [0.2.0] — 2026-05-18

### Fixed
- **DNS rebinding protection** (`enable_dns_rebinding_protection=False`): fix "Invalid Host header" / HTTP 421 error when connecting from remote clients (e.g. Hermes Agent WebUI on `10.0.0.70:10000` connecting to MCP server on `10.0.0.70:18761`).
