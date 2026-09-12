import asyncio, time, uuid
from typing import Dict, Any, List
try:
    import numpy as np
except ImportError:
    np = None
try:
    import ccxt
except ImportError:
    ccxt = None
from backend.config import settings
from backend.services.exchange import exchange_service
from backend.services.okx_connect import okx_connect
TOP = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT","ADA/USDT","AVAX/USDT","DOGE/USDT","LINK/USDT","TON/USDT"]
def _ema(vals, span):
    if not vals: return []
    k = 2.0 / (span + 1.0)
    out = [float(vals[0])]
    for v in vals[1:]:
        out.append(float(v) * k + out[-1] * (1.0 - k))
    return out
class NativeSignalEngine:
    def __init__(self):
        self.running = False; self.daily_pnl_pct = 0.0; self.open_positions = 0
        self.last_signals: List[Dict[str, Any]] = []; self._ex = None
    def halo_ok(self):
        return self.daily_pnl_pct > -settings.MAX_DAILY_LOSS_PERCENT and self.open_positions < 3
    def _exchange(self):
        if self._ex is None and ccxt:
            self._ex = ccxt.okx({"enableRateLimit": True})
        return self._ex
    def _ohlcv(self, symbol, tf="5m", limit=80):
        try: return self._exchange().fetch_ohlcv(symbol, tf, limit=limit) if ccxt else None
        except Exception: return None
    @staticmethod
    def _atr(o, n=14):
        if len(o) < n+1: return None
        h = np.array([x[2] for x in o], float) if np else [x[2] for x in o]
        l = np.array([x[3] for x in o], float) if np else [x[3] for x in o]
        c = np.array([x[4] for x in o], float) if np else [x[4] for x in o]
        if np:
            tr = np.maximum(h[1:]-l[1:], np.maximum(abs(h[1:]-c[:-1]), abs(l[1:]-c[:-1])))
            return float(tr[-n:].mean())
        else:
            tr = [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1, len(c))]
            return sum(tr[-n:])/n if tr else None
    def scan_symbol(self, symbol):
        o = self._ohlcv(symbol, "5m", 80)
        if not o or len(o) < 40: return {}
        c = np.array([x[4] for x in o], float) if np else [x[4] for x in o]
        v = np.array([x[5] for x in o], float) if np else [x[5] for x in o]
        e9 = _ema(c, 9); e21 = _ema(c, 21)
        atr = self._atr(o)
        h = self._ohlcv(symbol, "1h", 60)
        f2 = False
        if h and len(h) >= 50:
            hc = np.array([x[4] for x in h], float) if np else [x[4] for x in h]
            hema = _ema(hc, 50)
            f2 = bool(hc[-1] > hema[-1])
        f1 = bool(v[-1] > (sum(v[-20:])/20) * 1.5) if len(v) >= 20 else False
        f3 = bool(abs(c[-1]-c[-2]) > atr * 0.3) if atr else False
        f4 = bool(e9[-1] > e21[-1])
        score = int(f1)+int(f2)+int(f3)+int(f4)
        cross_up = e9[-2] <= e21[-2] and e9[-1] > e21[-1]
        cross_dn = e9[-2] >= e21[-2] and e9[-1] < e21[-1]
        side = ""
        if cross_up and score >= 3: side = "buy"
        elif cross_dn and score <= 1: side = "sell"
        if not side: return {}
        return {"symbol": symbol, "action": side, "price": float(c[-1]), "qty": 0.0,
                "interval": "5m", "time_ms": int(time.time()*1000), "nonce": uuid.uuid4().hex,
                "source": "native_quant", "score": score}
    async def route(self, sig):
        if exchange_service.killed: return {"routed": False, "reason": "kill-switch actif"}
        if not self.halo_ok(): return {"routed": False, "reason": "HALO : risque journalier / positions max"}
        qty = max(settings.MIN_ORDER_USDT / max(sig["price"], 1e-9), 1e-6)
        sig["qty"] = round(qty, 8)
        self.last_signals.insert(0, sig); del self.last_signals[50:]
        if settings.TRADING_MODE == "paper":
            res = exchange_service.place_order(sig["symbol"], sig["action"], qty, "market", sig["price"])
            return {"routed": True, "via": "paper", "order": res}
        if okx_connect.can_trade():
            res = exchange_service.place_order(sig["symbol"], sig["action"], qty, "market", sig["price"])
            return {"routed": True, "via": "okx_direct", "order": res}
        if okx_connect.status()["signalbot"]:
            res = await okx_connect.push_signal(sig)
            return {"routed": res.get("success"), "via": "okx_signalbot", "push": res}
        return {"routed": False, "reason": "LIVE verrouille : aucun connecteur OKX"}
    async def loop(self):
        self.running = True
        while self.running:
            for sym in TOP:
                sig = self.scan_symbol(sym)
                if sig: await self.route(sig)
                await asyncio.sleep(0.25)
            await asyncio.sleep(60)
native_engine = NativeSignalEngine()
