from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import timedelta, datetime, timezone
import asyncio, hmac, hashlib, json, time
import secrets as _secrets
from backend.config import settings
from backend.auth import create_access_token, get_current_user, check_rate_limit, record_attempt, pwd_context
from backend.services.agents import get_all_agents, agent_response
from backend.services.academy import get_levels
from backend.services.exchange import exchange_service
from backend.services.quant import quant_core, RISK_RULES
from backend.services.testimonials import get_all as get_testimonials, get_random as get_random_testimonial
from backend.services.jarvis import jarvis_brain
from backend.services.llm import ask_deep
from backend.services.okx_connect import okx_connect
from backend.services.signals_native import native_engine
from backend.services.freqtrade_bridge import ft_bridge
from backend.services.verification_gate import verification_gate
app = FastAPI(title="UberOKX", docs_url=None if settings.ENVIRONMENT == "production" else "/docs", redoc_url=None)
@app.middleware("http")
async def security_headers(request: Request, call_next):
    r = await call_next(request)
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.ENVIRONMENT == "production":
        r.headers["Strict-Transport-Security"] = "max-age=31536000"
    return r
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
ALERTS = []
def push_alert(title, body, level="info"):
    ALERTS.insert(0, {"title": title, "body": body, "level": level, "ts": datetime.now(timezone.utc).isoformat()})
    if len(ALERTS) > 50: ALERTS.pop()
@app.get("/manifest.json")
async def manifest():
    return FileResponse(BASE_DIR / "static" / "manifest.json", media_type="application/manifest+json")
@app.get("/sw.js")
async def sw():
    return FileResponse(BASE_DIR / "static" / "sw.js", media_type="application/javascript")
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    token = request.cookies.get("access_token")
    if token:
        try:
            from jose import jwt
            p = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if p.get("sub") == settings.ADMIN_EMAIL: return RedirectResponse("/dashboard")
        except Exception:
            pass
    return RedirectResponse("/login")
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if not settings.ADMIN_PASSWORD_HASH:
        return templates.TemplateResponse("login.html", {"request": request,
            "error": "Mot de passe non configure : renseigne ADMIN_PASSWORD_HASH (hash bcrypt) dans .env"})
    return templates.TemplateResponse("login.html", {"request": request, "error": None})
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(ip):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Trop de tentatives"}, status_code=429)
    if email == settings.ADMIN_EMAIL and pwd_context.verify(password, settings.ADMIN_PASSWORD_HASH):
        token = create_access_token({"sub": email}, timedelta(hours=12))
        status_code=303)
        resp.set_cookie("access_token", token, httponly=True,
                        secure=settings.ENVIRONMENT == "production", samesite="strict", max_age=12*3600)
        return resp
    record_attempt(ip)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants incorrects"}, status_code=401)
@app.get("/logout")
async def logout():
    r = RedirectResponse("/login"); r.delete_cookie("access_token"); return r
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user,
        "trading_mode": settings.TRADING_MODE, "agents": get_all_agents(), "levels": get_levels(),
        "testimonial": get_random_testimonial()})
@app.get("/api/status")
async def status(user: dict = Depends(get_current_user)):
    st = exchange_service.status()
    st["bridge"] = ft_bridge.status()
    st["engine"] = {"running": native_engine.running, "last_signals": native_engine.last_signals[:5]}
    st["verification"] = verification_gate.status()
    st["quant"] = quant_core.status()
    return st
@app.get("/api/radar")
async def radar(user: dict = Depends(get_current_user)):
    return quant_core.radar_scan()
@app.post("/api/chat")
async def chat(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    lang = data.get("lang", "fr")
    if data.get("agent_id", "jarvis") == "jarvis":
        out = jarvis_brain.ask(data.get("question", ""), lang)
        reply = out["reply"]
        if data.get("deep", False) or out.get("fallback", False):
            gpt = await ask_deep(data.get("question", ""), lang)
            if gpt: reply += "\nJARVIS-deep : " + gpt
        return {"agent": "jarvis", "reply": reply, "ms": out["ms"]}
    return {"agent": data.get("agent_id"), "reply": agent_response(data.get("agent_id", "jarvis"), data.get("question", ""), lang)}
@app.get("/api/academy")
async def academy(user: dict = Depends(get_current_user)):
    return get_levels()
@app.get("/api/testimonials")
async def testimonials(user: dict = Depends(get_current_user)):
    return get_testimonials()
@app.get("/api/alerts")
async def alerts(user: dict = Depends(get_current_user)):
    return ALERTS[:20]
@app.post("/api/settings/risk")
async def set_risk(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    if "risk_pct" in data: RISK_RULES["max_risk_per_trade_pct"] = float(data["risk_pct"])
    if "max_positions" in data: RISK_RULES["max_open_positions"] = int(data["max_positions"])
    return {"success": True, "rules": RISK_RULES}
@app.post("/api/settings/mode")
async def set_mode(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    mode = str(data.get("mode", ""))
    res = exchange_service.set_mode(mode, confirm_live=bool(data.get("confirm_live", False)))
    push_alert("MODE", "mode -> " + str(res.get("mode")), "info" if res.get("success") else "error")
    return res
@app.post("/api/emergency/stop")
async def emergency_stop(user: dict = Depends(get_current_user)):
    res = exchange_service.emergency_stop()
    if ft_bridge.status()["running"]: ft_bridge.stop()
    push_alert("KILL-SWITCH", "arret d'urgence - retour PAPER", "error")
    return res
@app.post("/api/okx/keys")
async def okx_keys(request: Request, user: dict = Depends(get_current_user)):
    d = await request.json()
    return await okx_connect.set_keys(d.get("api_key",""), d.get("api_secret",""), d.get("passphrase",""))
@app.post("/api/okx/fast_connect")
async def okx_fast(request: Request, user: dict = Depends(get_current_user)):
    d = await request.json()
    return await okx_connect.fast_connect(d.get("api_key",""), d.get("api_secret",""), d.get("passphrase",""), d.get("demo", True))
@app.get("/api/okx/oauth/start")
async def okx_oauth_start(user: dict = Depends(get_current_user)):
    res = okx_connect.oauth_start(_secrets.token_urlsafe(16))
    if res.get("success"): return RedirectResponse(res["url"])
    return JSONResponse(res, status_code=400)
@app.get("/api/okx/oauth/callback")
async def okx_oauth_cb(code: str = "", state: str = ""):
    res = await okx_connect.oauth_callback(code, state)
    return RedirectResponse("/dashboard?okx_oauth=" + ("ok" if res.get("success") else "ko"))
@app.post("/api/okx/signalbot")
async def okx_signalbot(request: Request, user: dict = Depends(get_current_user)):
    d = await request.json()
    return okx_connect.set_signalbot(d.get("url",""), d.get("secret",""))
@app.post("/api/okx/wallet")
async def okx_wallet(request: Request, user: dict = Depends(get_current_user)):
    d = await request.json()
    return okx_connect.set_wallet(d.get("address",""), d.get("chain","evm"))
@app.post("/api/okx/dex/quote")
async def okx_dex_quote(request: Request, user: dict = Depends(get_current_user)):
    d = await request.json()
    return await okx_connect.dex_quote(d.get("chain_id","1"), d.get("from",""), d.get("to",""), d.get("amount",""))
@app.post("/api/freqtrade/start")
async def ft_start(request: Request, user: dict = Depends(get_current_user)):
    d = await request.json()
    res = ft_bridge.start(confirm_live=bool(d.get("confirm_live", False)))
    push_alert("FreqTrade", "start -> " + str(res.get("mode", res.get("reason"))), "info" if res.get("success") else "error")
    return res
@app.post("/api/freqtrade/stop")
async def ft_stop(user: dict = Depends(get_current_user)):
    return ft_bridge.stop()
@app.get("/api/freqtrade/status")
async def ft_status(user: dict = Depends(get_current_user)):
    return ft_bridge.status()
@app.post("/api/freqtrade/backtest")
async def ft_backtest(request: Request, user: dict = Depends(get_current_user)):
    d = await request.json()
    return ft_bridge.backtest(days=int(d.get("days", 30)))
@app.on_event("startup")
async def _start_engine():
    asyncio.create_task(native_engine.loop())
@app.get("/health")
async def health():
    return {"status": "ok", "app": "UberOKX", "mode": settings.TRADING_MODE}
WEBHOOK_NONCES = {}
WEBHOOK_HITS = {}
def _webhook_rate_limited(ip):
    now = time.time()
    hits = [t for t in WEBHOOK_HITS.get(ip, []) if now - t < 60]
    hits.append(now); WEBHOOK_HITS[ip] = hits
    return len(hits) > 30
@app.post("/webhook/signals")
async def webhook_signals(request: Request):
    ip = request.client.host if request.client else "unknown"
    if _webhook_rate_limited(ip): return JSONResponse({"error": "rate-limit"}, status_code=429)
    if not settings.WEBHOOK_HMAC_SECRET: return JSONResponse({"error": "webhook non configure"}, status_code=503)
    body = await request.body()
    expect = hmac.new(settings.WEBHOOK_HMAC_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(request.headers.get("X-UBX-Signature",""), expect):
        return JSONResponse({"error": "signature invalide"}, status_code=401)
    try:
        data = json.loads(body)
    except Exception:
        return JSONResponse({"error": "JSON invalide"}, status_code=400)
    ts = int(data.get("time_ms") or 0); now_ms = int(time.time()*1000)
    if abs(now_ms - ts) > 30000: return JSONResponse({"error": "timestamp expire"}, status_code=401)
    nonce = str(data.get("nonce") or "")
    if not nonce or nonce in WEBHOOK_NONCES: return JSONResponse({"error": "nonce rejoue"}, status_code=401)
    WEBHOOK_NONCES[nonce] = ts
    for k in [k for k, v in WEBHOOK_NONCES.items() if now_ms - v > 3_600_000]:
        WEBHOOK_NONCES.pop(k, None)
    symbol = str(data.get("symbol","")); action = str(data.get("action","")).lower()
    qty = float(data.get("qty") or 0); price = float(data.get("price") or 0)
    whitelist = [x.strip() for x in settings.WEBHOOK_SYMBOL_WHITELIST.split(",") if x.strip()]
    if whitelist and symbol not in whitelist: return JSONResponse({"error": "symbole hors whitelist"}, status_code=400)
    if action not in ("buy","sell") or qty <= 0 or not symbol:
        return JSONResponse({"error": "payload invalide"}, status_code=400)
    if qty * price > settings.MAX_ORDER_NOTIONAL_USDT:
        return JSONResponse({"error": "notionnel > plafond"}, status_code=400)
    return await native_engine.route({"symbol": symbol, "action": action, "price": price, "qty": qty,
        "interval": str(data.get("interval") or ""), "time_ms": ts, "nonce": nonce, "source": "inbound"})
