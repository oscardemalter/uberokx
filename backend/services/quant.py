import re, time
from typing import Dict, List, Any
from datetime import datetime, timezone
try:
    import ccxt, numpy as np
except ImportError:
    ccxt = None; np = None
TOP20_SYMBOLS = [("BTC/USDT","BTC/USDT:USDT"),("ETH/USDT","ETH/USDT:USDT"),("BNB/USDT","BNB/USDT:USDT"),
    ("SOL/USDT","SOL/USDT:USDT"),("XRP/USDT","XRP/USDT:USDT"),("ADA/USDT","ADA/USDT:USDT"),
    ("AVAX/USDT","AVAX/USDT:USDT"),("DOGE/USDT","DOGE/USDT:USDT"),("DOT/USDT","DOT/USDT:USDT"),
    ("LINK/USDT","LINK/USDT:USDT"),("TON/USDT","TON/USDT:USDT"),("TRX/USDT","TRX/USDT:USDT"),
    ("LTC/USDT","LTC/USDT:USDT"),("BCH/USDT","BCH/USDT:USDT"),("UNI/USDT","UNI/USDT:USDT"),
    ("ATOM/USDT","ATOM/USDT:USDT"),("NEAR/USDT","NEAR/USDT:USDT"),("APT/USDT","APT/USDT:USDT"),
    ("SHIB/USDT","SHIB/USDT:USDT"),("PEPE/USDT","PEPE/USDT:USDT")]
NAME_MAP = {"bitcoin":"BTC/USDT","btc":"BTC/USDT","ethereum":"ETH/USDT","eth":"ETH/USDT",
    "bnb":"BNB/USDT","solana":"SOL/USDT","sol":"SOL/USDT","xrp":"XRP/USDT","cardano":"ADA/USDT",
    "ada":"ADA/USDT","avax":"AVAX/USDT","doge":"DOGE/USDT","dot":"DOT/USDT","link":"LINK/USDT",
    "ton":"TON/USDT","trx":"TRX/USDT","ltc":"LTC/USDT","shib":"SHIB/USDT","pepe":"PEPE/USDT"}
RISK_RULES = {"max_risk_per_trade_pct":1.0,"max_daily_loss_pct":5.0,"max_open_positions":3,
    "min_reward_risk":1.5,"require_a_plus_setup":True,"no_revenge_trading":True}
def _sma(a, p):
    return float(np.mean(a[-p:])) if len(a) >= p and np is not None else None
def _rsi(c, period=14):
    if len(c) < period+1 or np is None: return None
    d = np.diff(c); g = np.where(d>0, d, 0.0); l = np.where(d<0, -d, 0.0)
    ag, al = np.mean(g[-period:]), np.mean(l[-period:])
    return 100.0 if al == 0 else float(100 - 100/(1+ag/al))
class RiskManager:
    def __init__(self):
        self.daily_pnl_pct = 0.0; self.open_positions = 0
    def can_trade(self, risk_pct=1.0):
        reasons, ok = [], True
        if risk_pct > RISK_RULES["max_risk_per_trade_pct"]: ok=False; reasons.append("Risque trop eleve")
        if self.open_positions >= RISK_RULES["max_open_positions"]: ok=False; reasons.append("Trop de positions")
        return {"allowed": ok, "reasons": reasons, "rules": RISK_RULES}
class SignalEngine:
    def __init__(self):
        self._cache = {}; self._ttl = 20; self._ex = None
    def _get_exchange(self):
        if self._ex: return self._ex
        if ccxt is None: return None
        try:
            ex = ccxt.okx({"enableRateLimit": True, "options": {"defaultType": "spot"}})
            ex.load_markets(); self._ex = ex; return ex
        except Exception:
            try:
                ex = ccxt.binance({"enableRateLimit": True}); self._ex = ex; return ex
            except Exception:
                return None
    def _fetch(self, sym, tf="15m", limit=60):
        ex = self._get_exchange()
        if not ex: return None
        k = f"{sym}:{tf}"; now = time.time()
        if k in self._cache:
            ts, data = self._cache[k]
            if now - ts < self._ttl: return data
        try:
            o = ex.fetch_ohlcv(sym, timeframe=tf, limit=limit)
            self._cache[k] = (now, o); return o
        except Exception:
            return None
    def _watch(self, spot, disp):
        o = self._fetch(spot, "15m", 40)
        if not o or len(o) < 25 or np is None: return None
        c = np.array([x[4] for x in o], dtype=float)
        rsi = _rsi(c, 14); pct = round((c[-1]-c[-2])/c[-2]*100, 3)
        return {"symbol": disp, "price": float(c[-1]), "pct": pct, "rsi": round(rsi,1) if rsi else None}
    def scan_radar(self):
        wl = []
        for spot, disp in TOP20_SYMBOLS:
            w = self._watch(spot, disp)
            if w: wl.append(w)
            time.sleep(0.08)
        return {"signals": [], "watchlist": wl, "scanned": len(wl), "ts": datetime.now(timezone.utc).isoformat()}
class QuantCore:
    def __init__(self):
        self.risk = RiskManager(); self.signals = SignalEngine()
    def status(self):
        return {"radar": "TOP 20 mondial", "risk_rules": RISK_RULES, "message": "Radar Quant online - temps reel"}
    def check_trade(self, r=1.0):
        return self.risk.can_trade(r)
    def radar_scan(self):
        return self.signals.scan_radar()
    def any_crypto(self, q):
        spot = NAME_MAP.get(q.lower()) or (q.upper() if "/" in q else None)
        if not spot: return {"error": "Symbole inconnu"}
        ex = self.signals._get_exchange()
        if not ex: return {"error": "Marche indisponible"}
        try:
            t = ex.fetch_ticker(spot)
            o = self.signals._fetch(spot, "15m", 60)
            rsi = None; up = False
            if o and len(o) > 25:
                c = np.array([x[4] for x in o], dtype=float); rsi = _rsi(c, 14); up = bool(c[-1] > _sma(c, 20))
            return {"symbol": spot, "price": t.get("last"), "pct": round(t.get("percentage") or 0, 2),
                    "rsi": round(rsi,1) if rsi else None, "trend_up": up}
        except Exception as e:
            return {"error": str(e)}
quant_core = QuantCore()
