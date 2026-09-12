"""
Main FastAPI application for UberOKX trading platform.
Handles authentication, webhook routing, API endpoints, and security headers.
"""

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import timedelta, datetime, timezone
import asyncio
import hmac
import hashlib
import json
import time
import secrets as _secrets
from jose import JWTError, jwt

from backend.config import settings
from backend.auth import (
    create_access_token,
    get_current_user,
    check_rate_limit,
    record_attempt,
    pwd_context,
)
from backend.services.agents import get_all_agents, agent_response
from backend.services.academy import get_levels
from backend.services.exchange import exchange_service
from backend.services.quant import quant_core, RISK_RULES
from backend.services.testimonials import (
    get_all as get_testimonials,
    get_random as get_random_testimonial,
)
from backend.services.jarvis import jarvis_brain
from backend.services.llm import ask_deep
from backend.services.okx_connect import okx_connect
from backend.services.signals_native import native_engine
from backend.services.freqtrade_bridge import ft_bridge
from backend.services.verification_gate import verification_gate


# Initialize FastAPI app
app = FastAPI(
    title="UberOKX",
    docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None,
)


# Security middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Static files and templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Alert system
ALERTS = []
WEBHOOK_NONCES = {}
WEBHOOK_HITS = {}


def push_alert(title: str, body: str, level: str = "info") -> None:
    """
    Add an alert to the alert queue.
    
    Args:
        title: Alert title
        body: Alert message body
        level: Alert level (info, warning, error)
    """
    ALERTS.insert(
        0,
        {
            "title": title,
            "body": body,
            "level": level,
            "ts": datetime.now(timezone.utc).isoformat(),
        },
    )
    # Keep only last 50 alerts
    if len(ALERTS) > 50:
        ALERTS.pop()


def _webhook_rate_limited(ip: str, max_hits: int = 30, window_seconds: int = 60) -> bool:
    """
    Check if webhook endpoint is rate limited for an IP.
    
    Args:
        ip: Client IP address
        max_hits: Maximum hits allowed in window
        window_seconds: Time window in seconds
        
    Returns:
        True if rate limited, False otherwise
    """
    now = time.time()
    # Clean old hits outside window and add new one
    WEBHOOK_HITS[ip] = [t for t in WEBHOOK_HITS.get(ip, []) if now - t < window_seconds]
    WEBHOOK_HITS[ip].append(now)
    return len(WEBHOOK_HITS[ip]) > max_hits


def _cleanup_webhook_nonces() -> None:
    """Remove expired webhook nonces older than 1 hour."""
    now_ms = int(time.time() * 1000)
    expired_keys = [k for k, v in WEBHOOK_NONCES.items() if now_ms - v > 3_600_000]
    for key in expired_keys:
        WEBHOOK_NONCES.pop(key, None)


# Public endpoints
@app.get("/manifest.json")
async def manifest():
    """Serve PWA manifest."""
    return FileResponse(
        BASE_DIR / "static" / "manifest.json",
        media_type="application/manifest+json",
    )


@app.get("/sw.js")
async def sw():
    """Serve service worker."""
    return FileResponse(
        BASE_DIR / "static" / "sw.js", media_type="application/javascript"
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": "UberOKX",
        "mode": settings.TRADING_MODE,
    }


# Authentication endpoints
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirect authenticated users to dashboard."""
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("sub") == settings.ADMIN_EMAIL:
                return RedirectResponse("/dashboard", status_code=302)
        except JWTError:
            pass
    return RedirectResponse("/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page."""
    if not settings.ADMIN_PASSWORD_HASH:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Mot de passe non configuré: renseigne ADMIN_PASSWORD_HASH (hash bcrypt) dans .env",
            },
        )
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": None}
    )


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request, email: str = Form(...), password: str = Form(...)
):
    """Handle login POST request."""
    ip = request.client.host if request.client else "unknown"

    if not check_rate_limit(ip):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Trop de tentatives - réessayez dans 5 minutes"},
            status_code=429,
        )

    if email == settings.ADMIN_EMAIL and pwd_context.verify(
        password, settings.ADMIN_PASSWORD_HASH
    ):
        token = create_access_token({"sub": email}, timedelta(hours=12))
        response = RedirectResponse("/dashboard", status_code=302)
        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="strict",
            max_age=12 * 3600,
        )
        return response

    record_attempt(ip)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Identifiants incorrects"},
        status_code=401,
    )


@app.get("/logout")
async def logout():
    """Logout endpoint - clear auth cookie."""
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# Protected dashboard endpoint
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(get_current_user)):
    """Display main dashboard (requires authentication)."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "trading_mode": settings.TRADING_MODE,
            "agents": get_all_agents(),
            "levels": get_levels(),
            "testimonial": get_random_testimonial(),
        },
    )


# API endpoints
@app.get("/api/status")
async def status(user: dict = Depends(get_current_user)):
    """Get overall system status."""
    st = exchange_service.status()
    st["bridge"] = ft_bridge.status()
    st["engine"] = {
        "running": native_engine.running,
        "last_signals": native_engine.last_signals[:5],
    }
    st["verification"] = verification_gate.status()
    st["quant"] = quant_core.status()
    return st


@app.get("/api/radar")
async def radar(user: dict = Depends(get_current_user)):
    """Get quant radar scan data."""
    return quant_core.radar_scan()


@app.post("/api/chat")
async def chat(request: Request, user: dict = Depends(get_current_user)):
    """Handle chat requests with agents."""
    data = await request.json()
    lang = data.get("lang", "fr")

    if data.get("agent_id", "jarvis") == "jarvis":
        out = jarvis_brain.ask(data.get("question", ""), lang)
        reply = out["reply"]
        if data.get("deep", False) or out.get("fallback", False):
            gpt = await ask_deep(data.get("question", ""), lang)
            if gpt:
                reply += "\nJARVIS-deep : " + gpt
        return {"agent": "jarvis", "reply": reply, "ms": out["ms"]}

    return {
        "agent": data.get("agent_id", "jarvis"),
        "reply": agent_response(
            data.get("agent_id", "jarvis"),
            data.get("question", ""),
            lang,
        ),
    }


@app.get("/api/academy")
async def academy(user: dict = Depends(get_current_user)):
    """Get academy levels."""
    return get_levels()


@app.get("/api/testimonials")
async def testimonials(user: dict = Depends(get_current_user)):
    """Get testimonials."""
    return get_testimonials()


@app.get("/api/alerts")
async def alerts(user: dict = Depends(get_current_user)):
    """Get recent alerts."""
    return ALERTS[:20]


# Risk management endpoints
@app.post("/api/settings/risk")
async def set_risk(request: Request, user: dict = Depends(get_current_user)):
    """Update risk management settings."""
    data = await request.json()
    if "risk_pct" in data:
        RISK_RULES["max_risk_per_trade_pct"] = float(data["risk_pct"])
    if "max_positions" in data:
        RISK_RULES["max_open_positions"] = int(data["max_positions"])
    return {"success": True, "rules": RISK_RULES}


@app.post("/api/settings/mode")
async def set_mode(request: Request, user: dict = Depends(get_current_user)):
    """Change trading mode (paper/live)."""
    data = await request.json()
    mode = str(data.get("mode", "")).lower()
    res = exchange_service.set_mode(
        mode, confirm_live=bool(data.get("confirm_live", False))
    )
    push_alert(
        "MODE",
        "mode -> " + str(res.get("mode")),
        "info" if res.get("success") else "error",
    )
    return res


@app.post("/api/emergency/stop")
async def emergency_stop(user: dict = Depends(get_current_user)):
    """Emergency stop - stop all trading and return to PAPER mode."""
    res = exchange_service.emergency_stop()
    if ft_bridge.status().get("running"):
        ft_bridge.stop()
    push_alert("KILL-SWITCH", "arrêt d'urgence - retour PAPER", "error")
    return res


# OKX integration endpoints
@app.post("/api/okx/keys")
async def okx_keys(request: Request, user: dict = Depends(get_current_user)):
    """Set OKX API credentials."""
    data = await request.json()
    return await okx_connect.set_keys(
        data.get("api_key", ""),
        data.get("api_secret", ""),
        data.get("passphrase", ""),
    )


@app.post("/api/okx/fast_connect")
async def okx_fast(request: Request, user: dict = Depends(get_current_user)):
    """Fast OKX connection."""
    data = await request.json()
    return await okx_connect.fast_connect(
        data.get("api_key", ""),
        data.get("api_secret", ""),
        data.get("passphrase", ""),
        data.get("demo", True),
    )


@app.get("/api/okx/oauth/start")
async def okx_oauth_start(user: dict = Depends(get_current_user)):
    """Start OKX OAuth flow."""
    res = okx_connect.oauth_start(_secrets.token_urlsafe(16))
    if res.get("success"):
        return RedirectResponse(res["url"], status_code=302)
    return JSONResponse(res, status_code=400)


@app.get("/api/okx/oauth/callback")
async def okx_oauth_callback(code: str = "", state: str = ""):
    """OKX OAuth callback - requires no auth (external callback)."""
    res = await okx_connect.oauth_callback(code, state)
    status_param = "ok" if res.get("success") else "ko"
    return RedirectResponse(f"/dashboard?okx_oauth={status_param}", status_code=302)


@app.post("/api/okx/signalbot")
async def okx_signalbot(request: Request, user: dict = Depends(get_current_user)):
    """Configure OKX signal bot webhook."""
    data = await request.json()
    return okx_connect.set_signalbot(data.get("url", ""), data.get("secret", ""))


@app.post("/api/okx/wallet")
async def okx_wallet(request: Request, user: dict = Depends(get_current_user)):
    """Set OKX wallet address."""
    data = await request.json()
    return okx_connect.set_wallet(
        data.get("address", ""), data.get("chain", "evm")
    )


@app.post("/api/okx/dex/quote")
async def okx_dex_quote(request: Request, user: dict = Depends(get_current_user)):
    """Get OKX DEX quote."""
    data = await request.json()
    return await okx_connect.dex_quote(
        data.get("chain_id", "1"),
        data.get("from", ""),
        data.get("to", ""),
        data.get("amount", ""),
    )


# FreqTrade bridge endpoints
@app.post("/api/freqtrade/start")
async def ft_start(request: Request, user: dict = Depends(get_current_user)):
    """Start FreqTrade bot."""
    data = await request.json()
    res = ft_bridge.start(confirm_live=bool(data.get("confirm_live", False)))
    push_alert(
        "FreqTrade",
        "start -> " + str(res.get("mode", res.get("reason"))),
        "info" if res.get("success") else "error",
    )
    return res


@app.post("/api/freqtrade/stop")
async def ft_stop(user: dict = Depends(get_current_user)):
    """Stop FreqTrade bot."""
    return ft_bridge.stop()


@app.get("/api/freqtrade/status")
async def ft_status(user: dict = Depends(get_current_user)):
    """Get FreqTrade status."""
    return ft_bridge.status()


@app.post("/api/freqtrade/backtest")
async def ft_backtest(request: Request, user: dict = Depends(get_current_user)):
    """Run FreqTrade backtest."""
    data = await request.json()
    return ft_bridge.backtest(days=int(data.get("days", 30)))


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup."""
    asyncio.create_task(native_engine.loop())


# Webhook endpoint (no auth required, but has HMAC signature verification)
@app.post("/webhook/signals")
async def webhook_signals(request: Request):
    """
    Receive trading signals from external sources.
    Validates HMAC signature and prevents replay attacks.
    """
    ip = request.client.host if request.client else "unknown"

    # Rate limiting
    if _webhook_rate_limited(ip):
        return JSONResponse(
            {"error": "rate-limit"}, status_code=429
        )

    # Check webhook is configured
    if not settings.WEBHOOK_HMAC_SECRET:
        return JSONResponse(
            {"error": "webhook non configuré"}, status_code=503
        )

    # Verify HMAC signature
    body = await request.body()
    expected_signature = hmac.new(
        settings.WEBHOOK_HMAC_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        request.headers.get("X-UBX-Signature", ""), expected_signature
    ):
        return JSONResponse(
            {"error": "signature invalide"}, status_code=401
        )

    # Parse JSON payload
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return JSONResponse({"error": "JSON invalide"}, status_code=400)

    # Check timestamp (prevent replay attacks)
    ts = int(data.get("time_ms") or 0)
    now_ms = int(time.time() * 1000)
    if abs(now_ms - ts) > 30000:
        return JSONResponse({"error": "timestamp expiré"}, status_code=401)

    # Check nonce (prevent replay attacks)
    nonce = str(data.get("nonce") or "")
    if not nonce or nonce in WEBHOOK_NONCES:
        return JSONResponse({"error": "nonce rejoué"}, status_code=401)

    WEBHOOK_NONCES[nonce] = ts
    _cleanup_webhook_nonces()

    # Validate signal data
    symbol = str(data.get("symbol", "")).strip()
    action = str(data.get("action", "")).strip().lower()
    qty = float(data.get("qty") or 0)
    price = float(data.get("price") or 0)

    # Check symbol whitelist
    whitelist = [
        x.strip()
        for x in settings.WEBHOOK_SYMBOL_WHITELIST.split(",")
        if x.strip()
    ]
    if whitelist and symbol not in whitelist:
        return JSONResponse(
            {"error": "symbole hors whitelist"}, status_code=400
        )

    # Validate payload
    if action not in ("buy", "sell") or qty <= 0 or not symbol:
        return JSONResponse(
            {"error": "payload invalide"}, status_code=400
        )

    # Check notional value limit
    if qty * price > settings.MAX_ORDER_NOTIONAL_USDT:
        return JSONResponse(
            {"error": "notionnel > plafond"}, status_code=400
        )

    # Route to native engine
    return await native_engine.route(
        {
            "symbol": symbol,
            "action": action,
            "price": price,
            "qty": qty,
            "interval": str(data.get("interval") or ""),
            "time_ms": ts,
            "nonce": nonce,
            "source": "inbound",
        }
    )
