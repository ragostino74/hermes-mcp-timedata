#!/usr/bin/env python3
"""
Hermes MCP Server v0.1.0 — Time Data & Datetime Utilities

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

Modi di esecuzione:
  # STDIO (default — per Claude Desktop, VS Code, Hermes Agent)
  python hermes_mcp_timedata.py

  # HTTP/StreamableHTTP (per llama.cpp WebUI e browser)
  HERMES_MCP_TRANSPORT=http HERMES_MCP_PORT=18762 \
    python hermes_mcp_timedata.py

  # DUAL (entrambi insieme)
  HERMES_MCP_TRANSPORT=dual HERMES_MCP_PORT=18762 \
    python hermes_mcp_timedata.py

Variabili d'ambiente:
  HERMES_MCP_PORT       : Porta HTTP MCP (default: 18762)
  HERMES_MCP_TRANSPORT : stdio | http | dual (default: stdio)
  HERMES_MCP_BIND_ADDR  : Bind IP MCP HTTP (default: 127.0.0.1)
  HERMES_MCP_CORS_ORIGINS : CORS origins comma-separated (default: localhost:*)
"""
import json, sys, os, re, asyncio, signal as sig_mod
from datetime import datetime, timezone

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, InitializeRequest
    try:
        from mcp.types import MethodTypes
    except ImportError:
        MethodTypes = None
except ImportError as e:
    print(f"ERROR: Cannot import MCP packages: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from mcp.server.fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

TRANSPORT = os.environ.get("HERMES_MCP_TRANSPORT", "stdio")
_MCP_BIND_ADDR = os.environ.get("HERMES_MCP_BIND_ADDR", "127.0.0.1")
_CORS_RAW = os.environ.get("HERMES_MCP_CORS_ORIGINS", "")

# ── Italian timezone helper ──────────────────────────────
try:
    import zoneinfo
    _TIMEZONE = zoneinfo.ZoneInfo("Europe/Rome")
except Exception:
    from datetime import timezone as _tz, timedelta as _td
    class _CET(_tz):
        def utcoffset(self, dt): return _td(hours=1)
        def dst(self, dt): return _td(hours=0)
        def tzname(self, dt): return "CET"
    _TIMEZONE = _CET("CET")

_DAYS_IT = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]
_MONTHS_IT = [
    "gennaio","febbraio","marzo","aprile","maggio","giugno",
    "luglio","agosto","settembre","ottobre","novembre","dicembre",
]


# ── FastMCP server instance ──────────────────────────────
try:
    from mcp.server.transport_security import TransportSecuritySettings
except ImportError:
    TransportSecuritySettings = None

if FASTMCP_AVAILABLE and TransportSecuritySettings is not None:
    mcp_server = FastMCP(
        name="hermes-timedata-mcp",
        host=_MCP_BIND_ADDR,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
        ),
    )
else:
    mcp_server = FastMCP(name="hermes-timedata-mcp")


@mcp_server.tool()
async def get_current_datetime() -> str:
    """Ottieni la data e ora attuale in formato italiano (Europe/Rome)."""
    now = datetime.now(_TIMEZONE)
    return json.dumps({
        "date": f"{_DAYS_IT[now.weekday()]}, {now.day} {_MONTHS_IT[now.month - 1]} {now.year}",
        "time": now.strftime("%H:%M:%S"),
        "full_datetime": f"{_DAYS_IT[now.weekday()]} {now.day} {_MONTHS_IT[now.month - 1]} {now.year} alle {now.strftime('%H:%M:%S')}",
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
        "full_datetime": f"{_DAYS_IT[now.weekday()]} {now.day} {_MONTHS_IT[now.month - 1]} {now.year} alle {now.strftime('%H:%M:%S')} UTC",
        "timezone": "UTC",
        "iso": now.isoformat(),
        "timestamp": int(now.timestamp()),
        "week_number": now.isocalendar()[1],
    }, ensure_ascii=False)


@mcp_server.tool()
async def get_current_datetime_tz(timezone_name: str) -> str:
    """Ottieni la data e ora attuale per un fuso orario IANA specificato (es. 'America/New_York', 'Asia/Tokyo')."""
    timezone_name = timezone_name.strip()
    if not timezone_name:
        return json.dumps({"error": "Fuso orario richiesto"}, indent=2)
    try:
        tz = zoneinfo.ZoneInfo(timezone_name)
    except (zoneinfo.ZoneInfoNotFoundError, KeyError):
        return json.dumps({
            "error": f"Fuso orario non valido: '{timezone_name}'",
            "hint": "Usa fusi IANA come 'Europe/London', 'America/New_York', 'Asia/Tokyo'"
        }, indent=2)

    now = datetime.now(tz)
    return json.dumps({
        "date": f"{_DAYS_IT[now.weekday()]}, {now.day} {_MONTHS_IT[now.month - 1]} {now.year}",
        "time": now.strftime("%H:%M:%S"),
        "full_datetime": f"{_DAYS_IT[now.weekday()]} {now.day} {_MONTHS_IT[now.month - 1]} {now.year} alle {now.strftime('%H:%M:%S')}",
        "timezone": timezone_name,
        "iso": now.isoformat(),
        "timestamp": int(now.timestamp()),
        "week_number": now.isocalendar()[1],
    }, ensure_ascii=False)


@mcp_server.tool()
async def timestamp_to_datetime(unix_timestamp: float) -> str:
    """Converte un Unix timestamp a data/ora leggibile in italiano (Europe/Rome)."""
    try:
        ts = float(unix_timestamp)
    except (ValueError, TypeError):
        return json.dumps({"error": "Timestamp deve essere un numero"}, indent=2)

    try:
        now = datetime.fromtimestamp(ts, tz=_TIMEZONE)
        return json.dumps({
            "date": f"{_DAYS_IT[now.weekday()]}, {now.day} {_MONTHS_IT[now.month - 1]} {now.year}",
            "time": now.strftime("%H:%M:%S"),
            "full_datetime": f"{_DAYS_IT[now.weekday()]} {now.day} {_MONTHS_IT[now.month - 1]} {now.year} alle {now.strftime('%H:%M:%S')}",
            "timezone": "Europe/Rome",
            "iso": now.isoformat(),
            "timestamp": int(ts),
            "utc_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        }, ensure_ascii=False)
    except (OSError, OverflowError, ValueError):
        return json.dumps({"error": f"Timestamp non valido: {unix_timestamp}"}, indent=2)


@mcp_server.tool()
async def datetime_to_timestamp(
    date: str = "",
    time: str = "",
    format: str = ""
) -> str:
    """Converte una data/ora a Unix timestamp.

    Accetta date in formato ISO (es. '2025-05-17T14:30:00') oppure
    i parametri separati 'date' (YYYY-MM-DD) e 'time' (HH:MM:SS).
    Il formato custom supporta direttive Python (es. '%d/%m/%Y %H:%M').
    """
    dt_str = ""
    if date and time:
        dt_str = f"{date.strip()} {time.strip()}"
    elif date and not format:
        dt_str = date.strip()
    elif format and date:
        # Custom format parsing
        try:
            parsed = datetime.strptime(date.strip(), format)
            return json.dumps({
                "date": f"{_DAYS_IT[parsed.weekday()]}, {parsed.day} {_MONTHS_IT[parsed.month - 1]} {parsed.year}",
                "time": parsed.strftime("%H:%M:%S"),
                "timestamp": int(parsed.replace(tzinfo=_TIMEZONE if parsed.tzinfo is None else parsed.tzinfo).timestamp()),
                "iso": parsed.isoformat(),
            }, ensure_ascii=False)
        except ValueError as e:
            return json.dumps({"error": f"Formato non valido: {e}"}, indent=2)
    else:
        return json.dumps({
            "error": "Specificare almeno un parametro: 'date' (ISO o custom), o 'date' + 'time', con 'format' opzionale"
        }, indent=2)

    try:
        # Try ISO format first
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_TIMEZONE)
        ts = int(dt.timestamp())
        return json.dumps({
            "date": f"{_DAYS_IT[dt.weekday()]}, {dt.day} {_MONTHS_IT[dt.month - 1]} {dt.year}",
            "time": dt.strftime("%H:%M:%S"),
            "full_datetime": f"{_DAYS_IT[dt.weekday()]} {dt.day} {_MONTHS_IT[dt.month - 1]} {dt.year} alle {dt.strftime('%H:%M:%S')}",
            "timezone": str(dt.tzinfo),
            "iso": dt.isoformat(),
            "timestamp": ts,
            "utc_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        }, ensure_ascii=False)
    except (ValueError, TypeError) as e:
        return json.dumps({"error": f"Data/ora non valida: {e}\nUsa formato ISO (es. 2025-05-17T14:30:00)"}, indent=2)


# ── CORS configuration ───────────────────────────────────
if _CORS_RAW.lower() == "[]":
    cors_origins_list: list[str] = []
elif _CORS_RAW:
    cors_origins_list = [o.strip() for o in _CORS_RAW.split(",") if o.strip()]
else:
    cors_origins_list = ["http://localhost:*", "https://localhost:*"]


# ── Startup helpers ──────────────────────────────────────

async def main():
    print(f"🔮 Hermes TimeData MCP Server v0.1.0", file=sys.stderr)
    print(f"   Transport: {TRANSPORT}", file=sys.stderr)

    if TRANSPORT == "stdio":
        print("\nRunning in STDIO mode...", file=sys.stderr)
        await mcp_server.run_stdio_async()

    elif TRANSPORT in ("http", "dual"):
        port = int(os.environ.get("HERMES_MCP_PORT", "18762"))

        if FASTMCP_AVAILABLE:
            print(f"\nRunning in HTTP (StreamableHTTP) mode on :{port}...", file=sys.stderr)

            from starlette.applications import Starlette
            from starlette.routing import Mount
            from starlette.middleware.cors import CORSMiddleware

            mcp_app = mcp_server.streamable_http_app()

            cors_app = CORSMiddleware(
                app=mcp_app,
                allow_origins=cors_origins_list,
                allow_methods=["POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
                expose_headers=["Mcp-Session-Id", "Cache-Control", "Content-Disposition"],
            )

            import uvicorn
            config = uvicorn.Config(cors_app, host=_MCP_BIND_ADDR, port=port, log_level="info")
            server = uvicorn.Server(config)

            _shutdown_event = asyncio.Event()
            _mcpx_flag = False

            def _on_signal(_sig, _frame):
                print("\nShutting down...", file=sys.stderr)
                _shutdown_event.set()

            sig_mod.signal(sig_mod.SIGINT, _on_signal)
            sig_mod.signal(sig_mod.SIGTERM, _on_signal)

            try:
                await server.serve()
            except SystemExit as e:
                print(f"\nMCP HTTP server exited (code {e.code})", file=sys.stderr)
                if e.code != 0:
                    _mcpx_flag = True

            if _mcpx_flag:
                await _shutdown_event.wait()

            if _shutdown_event.is_set():
                print("Shutting down...", file=sys.stderr)

        else:
            print(
                "\nERROR: FastMCP with HTTP requires 'mcp[serve]' package.",
                file=sys.stderr,
            )
            print("Install with: pip install 'mcp[serve]'", file=sys.stderr)

    elif TRANSPORT == "dual" and not FASTMCP_AVAILABLE:
        print(
            "\nDual mode requires mcp[serve]. Falling back to stdio.",
            file=sys.stderr,
        )
        await mcp_server.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
