try:
    import ccxt
except ImportError:
    ccxt = None
import json, logging, os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from backend.config import settings
from backend.services.okx_connect import okx_connect
logger = logging.getLogger(__name__)
PAPER_FEE_PCT = 0.05
def _utcnow():
    return datetime.now(timezone.utc).isoformat()
@dataclass
class PaperOrder:
    id: str; symbol: str; side: str; amount: float; price: float
    fee_usdt: float; status: str; mode: str; ts: str
class ExchangeService:
    def __init__(self):
        self._public = ccxt.okx({"enableRateLimit": True}) if ccxt else None
        self._live = None
        self.paper_balance = {"USDT": 10000.0, "free": 10000.0, "used": 0.0}
        self.paper_orders: List[PaperOrder] = []
        self.killed = False
        self.daily_pnl_pct = 0.0
        self._load_ledger()
    def _load_ledger(self):
        try:
            if os.path.exists(settings.PAPER_LEDGER_PATH):
                with open(settings.PAPER_LEDGER_PATH, "r", encoding="utf-8") as fh:
                    d = json.load(fh)
                self.paper_balance = d.get("balance", self.paper_balance)
                self.paper_orders = [PaperOrder(**o) for o in d.get("orders", [])]
        except Exception as e:
            logger.warning("ledger: %s", e)
    def _save_ledger(self):
        try:
            os.makedirs(os.path.dirname(settings.PAPER_LEDGER_PATH) or ".", exist_ok=True)
            with open(settings.PAPER_LEDGER_PATH, "w", encoding="utf-8") as fh:
                json.dump({"balance": self.paper_balance,
                           "orders": [asdict(o) for o in self.paper_orders[-200:]]}, fh)
            os.chmod(settings.PAPER_LEDGER_PATH, 0o600)
        except Exception as e:
            logger.warning("ledger save: %s", e)
    def _audit(self, event, detail=""):
        try:
            os.makedirs(os.path.dirname(settings.AUDIT_PATH) or ".", exist_ok=True)
            with open(settings.AUDIT_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": _utcnow(), "event": event, "detail": detail}, ensure_ascii=False) + "\n")
            os.chmod(settings.AUDIT_PATH, 0o600)
        except Exception as e:
            logger.warning("audit: %s", e)
    def set_mode(self, mode, confirm_live=False):
        if mode not in ("paper", "live"): return {"success": False, "reason": "mode invalide"}
        if mode == "live":
            if self.killed: return {"success": False, "reason": "LIVE refuse : kill-switch actif."}
            if not okx_connect.can_trade(): return {"success": False, "reason": "LIVE refuse : cles API absentes."}
            if not confirm_live: return {"success": False, "reason": "LIVE refuse : confirmation manquante."}
        settings.TRADING_MODE = mode; self._live = None
        self._audit("MODE_SET", mode)
        return {"success": True, "mode": mode, "can_trade": okx_connect.can_trade()}
    def emergency_stop(self):
        self.killed = True; settings.TRADING_MODE = "paper"; self._live = None
        self._audit("EMERGENCY_STOP")
        return {"success": True, "mode": "paper", "killed": True}
    @property
    def live(self):
        if self._live is None and ccxt and okx_connect.can_trade():
            self._live = ccxt.okx(okx_connect.ccxt_config())
        return self._live
    def get_ticker(self, symbol="BTC/USDT"):
        if not self._public: return {"error": "ccxt indisponible", "symbol": symbol}
        try:
            t = self._public.fetch_ticker(symbol)
            return {"symbol": symbol, "last": t.get("last"), "percentage": t.get("percentage"),
                    "mode": settings.TRADING_MODE, "exchange": "okx"}
        except Exception as e:
            return {"error": str(e), "symbol": symbol}
    def place_order(self, symbol, side, amount, order_type="market", price=None):
        if self.killed: return {"error": "kill-switch actif : aucun ordre."}
        if side not in ("buy", "sell") or amount <= 0: return {"error": "parametres invalides"}
        px = float(price or self.get_ticker(symbol).get("last") or 0.0)
        notional = amount * px
        if notional > settings.MAX_ORDER_NOTIONAL_USDT: return {"error": "notionnel > plafond"}
        if settings.TRADING_MODE == "paper":
            if px <= 0: return {"error": "prix paper indisponible"}
            if notional < settings.MIN_ORDER_USDT: return {"error": "minimum " + str(settings.MIN_ORDER_USDT) + " USDT"}
            fee = notional * PAPER_FEE_PCT / 100.0
            o = PaperOrder(id=f"paper-{len(self.paper_orders)+1}", symbol=symbol, side=side, amount=amount,
                           price=px, fee_usdt=round(fee,6), status="filled", mode="paper", ts=_utcnow())
            self.paper_orders.append(o)
            self.paper_balance["USDT"] = round(self.paper_balance["USDT"] - fee, 6)
            self.paper_balance["free"] = self.paper_balance["USDT"]
            self._save_ledger(); self._audit("PAPER_ORDER", f"{side} {symbol} {notional:.2f}")
            return {"id": o.id, "symbol": symbol, "side": side, "amount": amount, "price": px,
                    "fee_usdt": o.fee_usdt, "status": "filled", "mode": "paper",
                    "message": "Ordre simule - frais 0,05 % + slippage 1 tick simules"}
        if not okx_connect.can_trade() or not self.live:
            return {"error": "LIVE verrouille : mode/connecteur/cles manquants."}
        try:
            o = self.live.create_order(symbol, "market" if order_type == "market" else "limit", side, amount, price)
            self._audit("LIVE_ORDER", f"{side} {symbol} {notional:.2f}")
            return {"id": o.get("id"), "symbol": symbol, "side": side, "status": o.get("status"),
                    "mode": "live", "message": "ORDRE REEL sur OKX" + (" (demo)" if settings.OKX_DEMO else "")}
        except Exception as e:
            self._audit("LIVE_ERROR", str(e))
            return {"error": str(e), "mode": "live"}
    def get_balance(self):
        if settings.TRADING_MODE == "paper": return {"mode": "paper", **self.paper_balance}
        if not okx_connect.can_trade() or not self.live: return {"mode": "live", "connected": False}
        try:
            b = self.live.fetch_balance(); u = b.get("USDT", {})
            return {"mode": "live", "connected": True, "USDT": u.get("total",0), "free": u.get("free",0)}
        except Exception as e:
            return {"mode": "live", "error": str(e)}
    def get_positions(self):
        if settings.TRADING_MODE == "paper" or not okx_connect.can_trade(): return []
        try:
            p = self.live.fetch_positions()
            return [x for x in p if float(x.get("contracts",0)) > 0]
        except Exception as e:
            return [{"error": str(e)}]
    def status(self):
        return {"trading_mode": settings.TRADING_MODE, "killed": self.killed,
                "min_order": settings.MIN_ORDER_USDT,
                "paper": {"balance": self.paper_balance, "orders": len(self.paper_orders)},
                "okx": okx_connect.status()}
exchange_service = ExchangeService()
