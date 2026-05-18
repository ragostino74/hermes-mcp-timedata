#!/usr/bin/env python3
"""
Hermes MCP TimeData Server v0.2.2 — Time Data & Datetime Utilities

MCP (Model Context Protocol) server che espone strumenti per data/ora e conversioni:
  - get_current_datetime  : Data/ora attuale in formato italiano (Europe/Rome)
  - get_current_datetime_utc  : Data/ora attuale in UTC
  - get_current_datetime_tz : Data/ora per un fuso orario specificato
  - timestamp_to_datetime : Converte Unix timestamp a data/ora leggibile
  - datetime_to_timestamp : Converte data/ora a Unix timestamp

Caratteristiche:
  - Doppio trasporto: stdio (Claude Desktop, VS Code) + HTTP/StreamableHTTP
  - Supporto zoneinfo (con fallback CET manuale)
  - Validazione fusi orari IANA
  - HTTP binding configurabile (default: 127.0.0.1)
  - DNS rebinding protection abilitata con allowed_hosts configurabile
  - CORS configurabile via variabile d'ambiente

Modi di esecuzione:
  # STDIO (default — per Claude Desktop, VS Code, Hermes Agent)
  python hermes_mcp_timedata.py

  # HTTP/StreamableHTTP (per llama.cpp WebUI e browser)
  HERMES_MCP_TRANSPORT=http HERMES_MCP_PORT=18761 \
    python hermes_mcp_timedata.py

Variabili d'ambiente:
  HERMES_MCP_PORT          : Porta HTTP MCP (default: 18761)
  HERMES_MCP_TRANSPORT     : stdio | http | dual (default: stdio)
  HERMES_MCP_BIND_ADDR     : Bind IP MCP HTTP (default: 127.0.0.1)
  HERMES_MCP_CORS_ORIGINS  : CORS origins comma-separated
                             (default: http://localhost:*,https://localhost:*)
  HERMES_MCP_ALLOWED_HOSTS : Hosts consentiti per Host header check
                             (default: localhost,127.0.0.1,::1)
"""
import json, sys, os, asyncio, signal as sig_mod
from datetime import datetime, timezone
from typing import List, Optional

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("ERROR: mcp package non installato. Installare con: pip install mcp", file=sys.stderr)
    sys.exit(1)

TRANSPORT: str = os.environ.get("HERMES_MCP_TRANSPORT", "stdio")
BIND_ADDR: str = os.environ.get("HERMES_MCP_BIND_ADDR", "127.0.0.1")
_CORS_RAW: str = os.environ.get("HERMES_MCP_CORS_ORIGINS", "")
_ALLOWED_HOSTS_RAW: str = os.environ.get("HERMES_MCP_ALLOWED_HOSTS", "")

# ── Italian timezone helper ──────────────────────────────────────────
try:
    import zoneinfo
    _TIMEZONE = zoneinfo.ZoneInfo("Europe/Rome")
except Exception:
    from datetime import timezone as _tz, timedelta as _td
    class _CET(_tz):
        def utcoffset(self, dt):  # type: ignore
            return _td(hours=1)
        def dst(self, dt):  # type: ignore
            return _td(hours=0)
        def tzname(self, dt) -> str:
            return "CET"
    _TIMEZONE = _CET("CET")

_DAYS_IT: List[str] = [
    "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica",
]
_MONTHS_IT: List[str] = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]

# ── CORS configuration ───────────────────────────────────────────────
if _CORS_RAW.strip().lower() == "[]":
    CORS_ORIGINS: List[str] = []
elif _CORS_RAW.strip():
    CORS_ORIGINS = [o.strip() for o in _CORS_RAW.split(",") if o.strip()]
else:
    CORS_ORIGINS = ["http://localhost:*", "https://localhost:*"]

# ── Allowed hosts configuration ──────────────────────────────────────
if _ALLOWED_HOSTS_RAW.strip():
    ALLOWED_HOSTS: List[str] = [
        h.strip() for h in _ALLOWED_HOSTS_RAW.split(",") if h.strip()
    ]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "::1"]

# ── FastMCP server instance ──────────────────────────────────────────
# DNS rebinding protection is ENABLED by default.
# Configure allowed hosts via HERMES_MCP_ALLOWED_HOSTS if you need
# to connect from specific remote addresses.
mcp_server: FastMCP = FastMCP(
    name="hermes-timedata-mcp",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=ALLOWED_HOSTS,
    ),
)


@mcp_server.tool()
async def get_current_datetime() -> str:
    """Ottieni la data e ora attuale in formato italiano (Europe/Rome)."""
    now = datetime.now(_TIMEZONE)
    return json.dumps({
        "date": f"{_DAYS_IT[now.weekday()]}, {now.day} {_MONTHS_IT[now.month - 1]} {now.year}",
        "time": now.strftime("%H:%M:%S"),
        "full_datetime": (
            f"{_DAYS_IT[now.weekday()]} {now.day} {_MONTHS_IT[now.month - 1]} "
            f"{now.year} alle {now.strftime('%H:%M:%S')}"
        ),
        "timezone": "Europe/Rome",
        "iso": now.isoformat(),
        "timestamp": int(now.timestamp()),
        "week_number": now.isocalendar()[1],
    }, ensure_ascii=False)


@mcp_server.tool()
async def get_current_datetime_utc() -> str:
    """Ottieni la data e ora attuale in UTC."""
    now = datetime.now(timezone.utc)
    return json.dumps({
        "date": f"{_DAYS_IT[now.weekday()]}, {now.day} {_MONTHS_IT[now.month - 1]} {now.year}",
        "time": now.strftime("%H:%M:%S"),
        "full_datetime": (
            f"{_DAYS_IT[now.weekday()]} {now.day} {_MONTHS_IT[now.month - 1]} "
            f"{now.year} alle {now.strftime('%H:%M:%S')} UTC"
        ),
        "timezone": "UTC",
        "iso": now.isoformat(),
        "timestamp": int(now.timestamp()),
        "week_number": now.isocalendar()[1],
    }, ensure_ascii=False)


@mcp_server.tool()
async def get_current_datetime_tz(timezone_name: str) -> str:
    """Ottieni la data e ora attuale per un fuso orario IANA specificato
    (es. 'America/New_York', 'Asia/Tokyo')."""
    timezone_name = timezone_name.strip()
    if not timezone_name:
        return json.dumps({"error": "Fuso orario richiesto"}, indent=2)
    try:
        tz = zoneinfo.ZoneInfo(timezone_name)
    except (zoneinfo.ZoneInfoNotFoundError, KeyError):
        return json.dumps({
            "error": f"Fuso orario non valido: '{timezone_name}'",
            "hint": (
                "Usa fusi IANA come 'Europe/London', 'America/New_York', 'Asia/Tokyo'"
            ),
        }, indent=2)

    now = datetime.now(tz)
    return json.dumps({
        "date": f"{_DAYS_IT[now.weekday()]}, {now.day} {_MONTHS_IT[now.month - 1]} {now.year}",
        "time": now.strftime("%H:%M:%S"),
        "full_datetime": (
            f"{_DAYS_IT[now.weekday()]} {now.day} {_MONTHS_IT[now.month - 1]} "
            f"{now.year} alle {now.strftime('%H:%M:%S')}"
        ),
        "timezone": timezone_name,
        "iso": now.isoformat(),
        "timestamp": int(now.timestamp()),
        "week_number": now.isocalendar()[1],
    }, ensure_ascii=False)


@mcp_server.tool()
async def timestamp_to_datetime(unix_timestamp: float) -> str:
    """Converte un Unix timestamp a data/ora leggibile in italiano
    (Europe/Rome)."""
    try:
        ts = float(unix_timestamp)
    except (ValueError, TypeError):
        return json.dumps({"error": "Timestamp deve essere un numero"}, indent=2)

    try:
        now = datetime.fromtimestamp(ts, tz=_TIMEZONE)
        return json.dumps({
            "date": (
                f"{_DAYS_IT[now.weekday()]}, {now.day} "
                f"{_MONTHS_IT[now.month - 1]} {now.year}"
            ),
            "time": now.strftime("%H:%M:%S"),
            "full_datetime": (
                f"{_DAYS_IT[now.weekday()]} {now.day} "
                f"{_MONTHS_IT[now.month - 1]} {now.year} "
                f"alle {now.strftime('%H:%M:%S')}"
            ),
            "timezone": "Europe/Rome",
            "iso": now.isoformat(),
            "timestamp": int(ts),
            "utc_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        }, ensure_ascii=False)
    except (OSError, OverflowError, ValueError):
        return json.dumps(
            {"error": f"Timestamp non valido: {unix_timestamp}"}, indent=2
        )


@mcp_server.tool()
async def datetime_to_timestamp(
    date: str = "",
    time_val: str = "",
    fmt: str = "",
) -> str:
    """Converte una data/ora a Unix timestamp.

    Accetta date in formato ISO (es. '2025-05-17T14:30:00') oppure
    i parametri separati 'date' (YYYY-MM-DD) e 'time' (HH:MM:SS).
    Il formato custom supporta direttive Python (es. '%d/%m/%Y %H:%M').
    """
    dt_str = ""
    if date and time_val:
        dt_str = f"{date.strip()} {time_val.strip()}"
    elif date and not fmt:
        dt_str = date.strip()
    elif fmt and date:
        # Custom format parsing
        try:
            parsed = datetime.strptime(date.strip(), fmt)
            return json.dumps({
                "date": (
                    f"{_DAYS_IT[parsed.weekday()]}, {parsed.day} "
                    f"{_MONTHS_IT[parsed.month - 1]} {parsed.year}"
                ),
                "time": parsed.strftime("%H:%M:%S"),
                "timestamp": int(
                    parsed.replace(
                        tzinfo=_TIMEZONE if parsed.tzinfo is None else parsed.tzinfo
                    ).timestamp()
                ),
                "iso": parsed.isoformat(),
            }, ensure_ascii=False)
        except ValueError as e:
            return json.dumps({"error": f"Formato non valido: {e}"}, indent=2)
    else:
        return json.dumps({
            "error": (
                "Specificare almeno un parametro: 'date' (ISO o custom), "
                "o 'date' + 'time', con 'format' opzionale"
            ),
        }, indent=2)

    try:
        # Try ISO format first
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_TIMEZONE)
        ts = int(dt.timestamp())
        return json.dumps({
            "date": (
                f"{_DAYS_IT[dt.weekday()]}, {dt.day} "
                f"{_MONTHS_IT[dt.month - 1]} {dt.year}"
            ),
            "time": dt.strftime("%H:%M:%S"),
            "full_datetime": (
                f"{_DAYS_IT[dt.weekday()]} {dt.day} "
                f"{_MONTHS_IT[dt.month - 1]} {dt.year} "
                f"alle {dt.strftime('%H:%M:%S')}"
            ),
            "timezone": str(dt.tzinfo),
            "iso": dt.isoformat(),
            "timestamp": ts,
            "utc_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        }, ensure_ascii=False)
    except (ValueError, TypeError) as e:
        return json.dumps(
            {
                "error": (
                    f"Data/ora non valida: {e}\n"
                    "Usa formato ISO (es. 2025-05-17T14:30:00)"
                ),
            },
            indent=2,
        )


# ── Starlette / HTTP helpers ─────────────────────────────────────────
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint per sistemi di monitoraggio."""
    return JSONResponse({
        "status": "healthy",
        "version": "0.2.2",
        "transport": TRANSPORT,
        "bind_addr": BIND_ADDR,
    })


HEALTH_ROUTES: List[Route] = [
    Route("/health", health_check),
    Route("/health/", health_check),
]


async def main() -> None:
    print(f"🔮 Hermes TimeData MCP Server v0.2.2", file=sys.stderr)
    print(f"   Transport:    {TRANSPORT}", file=sys.stderr)
    print(f"   Bind addr:    {BIND_ADDR}", file=sys.stderr)
    print(f"   CORS origins: {CORS_ORIGINS}", file=sys.stderr)
    print(f"   Allowed hosts: {ALLOWED_HOSTS}", file=sys.stderr)

    if TRANSPORT == "stdio":
        print("\nRunning in STDIO mode...", file=sys.stderr)
        await mcp_server.run_stdio_async()

    elif TRANSPORT == "http":
        port = int(os.environ.get("HERMES_MCP_PORT", "18761"))
        if not FASTMCP_AVAILABLE:
            print(
                "\nERROR: FastMCP HTTP richiede 'mcp[serve]'.", file=sys.stderr
            )
            return

        print(
            f"\nRunning in HTTP (StreamableHTTP) mode on {BIND_ADDR}:{port}...",
            file=sys.stderr,
        )

        mcp_app = mcp_server.streamable_http_app()

        # Combine MCP routes + health routes, then wrap with CORS
        combined_app = Starlette(
            routes=[*mcp_app.routes, *HEALTH_ROUTES],
        )
        cors_app = CORSMiddleware(
            app=combined_app,
            allow_origins=CORS_ORIGINS,
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=[
                "Mcp-Session-Id",
                "Cache-Control",
                "Content-Disposition",
            ],
        )

        import uvicorn

        config = uvicorn.Config(
            cors_app,
            host=BIND_ADDR,
            port=port,
            log_level="info",
        )
        server = uvicorn.Server(config)

        _shutdown_event = asyncio.Event()

        def _on_signal(_sig: object, _frame: object) -> None:
            print("\nShutting down...", file=sys.stderr)
            _shutdown_event.set()

        sig_mod.signal(sig_mod.SIGINT, _on_signal)
        sig_mod.signal(sig_mod.SIGTERM, _on_signal)

        try:
            await server.serve()
        except SystemExit:
            pass

        if _shutdown_event.is_set():
            print("Shutting down...", file=sys.stderr)

    elif TRANSPORT == "dual":
        print(
            "\nRunning in DUAL mode (stdio + HTTP)...",
            file=sys.stderr,
        )

        if not FASTMCP_AVAILABLE:
            print(
                "\nDual mode requires mcp[serve]. Falling back to stdio.",
                file=sys.stderr,
            )
            await mcp_server.run_stdio_async()
            return

        port = int(os.environ.get("HERMES_MCP_PORT", "18761"))

        mcp_app = mcp_server.streamable_http_app()
        combined_app = Starlette(
            routes=[*mcp_app.routes, *HEALTH_ROUTES],
        )
        cors_app = CORSMiddleware(
            app=combined_app,
            allow_origins=CORS_ORIGINS,
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=[
                "Mcp-Session-Id",
                "Cache-Control",
                "Content-Disposition",
            ],
        )

        import uvicorn

        http_config = uvicorn.Config(
            cors_app,
            host=BIND_ADDR,
            port=port,
            log_level="info",
        )
        http_server = uvicorn.Server(http_config)

        _shutdown_event = asyncio.Event()

        def _on_signal(_sig: object, _frame: object) -> None:
            print("\nShutting down...", file=sys.stderr)
            _shutdown_event.set()

        sig_mod.signal(sig_mod.SIGINT, _on_signal)
        sig_mod.signal(sig_mod.SIGTERM, _on_signal)

        # Run stdio and HTTP concurrently
        stdio_task = asyncio.create_task(mcp_server.run_stdio_async())
        http_task = asyncio.create_task(http_server.serve())

        await asyncio.gather(stdio_task, http_task, return_exceptions=True)
        print("Shutting down...", file=sys.stderr)

    else:
        print(
            f"ERROR: Unknown transport '{TRANSPORT}'. "
            "Use stdio, http, or dual.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
