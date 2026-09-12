from flask import Flask, request, jsonify, send_from_directory, render_template_string, redirect, make_response, send_file
from datetime import datetime, timedelta, timezone
from pathlib import Path
from jose import jwt
import hmac, hashlib, json, time, secrets, asyncio
from backend.config import settings
from backend.auth import create_access_token, pwd_context
from backend.services.agents import get_all_agents
from backend.services.academy import get_levels
from backend.services.exchange import exchange_service
from backend.services.quant import quant_core
from backend.services.testimonials import get_random_testimonial
from backend.services.jarvis import jarvis_brain
from backend.services.okx_connect import okx_connect
from backend.services.signals_native import native_engine
from backend.services.freqtrade_bridge import ft_bridge
from backend.services.verification_gate import verification_gate
import threading

app = Flask(__name__, 
            template_folder=str(Path(__file__).parent / 'templates'),
            static_folder=str(Path(__file__).parent / 'static'),
            static_url_path='/static')

ALERTS = []

def push_alert(title, body, level="info"):
    ALERTS.insert(0, {"title": title, "body": body, "level": level, "ts": datetime.now(timezone.utc).isoformat()})
    if len(ALERTS) > 50: ALERTS.pop()

def get_current_user():
    token = request.cookies.get("access_token")
    if not token: return None
    try:
        p = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if p.get("sub") == settings.ADMIN_EMAIL: return {"email": settings.ADMIN_EMAIL}
    except: pass
    return None

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user: return redirect("/login")
        return f(*args, **kwargs)
    return decorated

@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "UberOKX", "mode": settings.TRADING_MODE})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email == settings.ADMIN_EMAIL and pwd_context.verify(password, settings.ADMIN_PASSWORD_HASH):
            token = create_access_token({"sub": email}, timedelta(hours=12))
            resp = redirect("/dashboard")
            resp.set_cookie("access_token", token, httponly=True, max_age=12*3600)
            return resp
        return "Identifiants incorrects", 401
    return render_template_string(open(Path(__file__).parent / 'templates' / 'login.html').read())

@app.route("/logout")
def logout():
    resp = redirect("/login")
    resp.delete_cookie("access_token")
    return resp

@app.route("/dashboard")
@require_auth
def dashboard():
    template = open(Path(__file__).parent / 'templates' / 'dashboard.html').read()
    return render_template_string(template,
        trading_mode=settings.TRADING_MODE, 
        agents=get_all_agents(), 
        levels=get_levels(),
        testimonial=get_random_testimonial())

@app.route("/api/status")
@require_auth
def api_status():
    return jsonify({
        "trading_mode": settings.TRADING_MODE,
        "bridge": ft_bridge.status(),
        "verification": verification_gate.status(),
        "quant": quant_core.status()
    })

@app.route("/api/radar")
@require_auth
def api_radar():
    return jsonify(quant_core.radar_scan())

@app.route("/api/chat", methods=["POST"])
@require_auth
def api_chat():
    data = request.json
    out = jarvis_brain.ask(data.get("question", ""), data.get("lang", "fr"))
    return jsonify({"agent": "jarvis", "reply": out["reply"], "ms": out["ms"]})

@app.route("/api/academy")
@require_auth
def api_academy():
    return jsonify(get_levels())

@app.route("/api/settings/mode", methods=["POST"])
@require_auth
def api_set_mode():
    data = request.json
    res = exchange_service.set_mode(data.get("mode", "paper"), confirm_live=data.get("confirm_live", False))
    return jsonify(res)

@app.route("/api/emergency/stop", methods=["POST"])
@require_auth
def api_emergency():
    res = exchange_service.emergency_stop()
    return jsonify(res)

if __name__ == "__main__":
    print("=" * 60)
    print("  ÜBEROKX - Plateforme Trading AI")
    print("  Mode: PAPER (simulé)")
    print("  Accès: http://127.0.0.1:8080")
    print("=" * 60)
    app.run(host="127.0.0.1", port=8080, debug=False, threaded=True)
