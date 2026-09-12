import hmac
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
from backend.config import settings


class TradingViewWebhook:
    """Gestion des webhooks TradingView pour UberOKX"""
    
    def __init__(self):
        self.webhook_log_path = Path("data/tradingview_webhooks.jsonl")
        self.webhook_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.received_signals = []
        
    def verify_signature(self, payload: str, signature: str) -> bool:
        """Vérifie la signature HMAC du webhook TradingView"""
        if not settings.TRADINGVIEW_WEBHOOK_SECRET:
            return True  # Mode débug sans vérification
        
        expected = hmac.new(
            settings.TRADINGVIEW_WEBHOOK_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    def parse_signal(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse le signal TradingView"""
        try:
            symbol = data.get("symbol", "")
            if not symbol:
                return None
            
            # Convertir BTCUSDT -> BTC/USDT
            if "/" not in symbol:
                if "USDT" in symbol:
                    base = symbol.replace("USDT", "")
                    symbol = f"{base}/USDT"
            
            action = data.get("action", "").lower()
            if action not in ["buy", "sell", "long", "short"]:
                return None
            
            if action in ["long"]:
                action = "buy"
            elif action in ["short"]:
                action = "sell"
            
            price = float(data.get("price", 0))
            qty = float(data.get("qty", 0))
            
            if qty == 0 and price > 0:
                qty = settings.MIN_ORDER_USDT / price
            
            signal = {
                "symbol": symbol,
                "action": action,
                "price": price,
                "qty": round(qty, 8),
                "strategy": data.get("strategy", "tradingview"),
                "timestamp": data.get("timestamp", int(time.time() * 1000)),
                "source": "tradingview_webhook",
                "nonce": f"tv_{int(time.time() * 1000)}"
            }
            
            whitelist = [x.strip() for x in settings.WEBHOOK_SYMBOL_WHITELIST.split(",")]
            if symbol not in whitelist:
                signal["warning"] = f"Symbole {symbol} hors whitelist"
            
            return signal
            
        except Exception as e:
            print(f"Error parsing signal: {e}")
            return None
    
    def log_webhook(self, data: Dict[str, Any], verified: bool):
        """Log les webhooks reçus"""
        log_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "verified": verified,
            "data": data
        }
        
        with open(self.webhook_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        self.received_signals.insert(0, log_entry)
        if len(self.received_signals) > 1000:
            self.received_signals.pop()
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut des webhooks"""
        return {
            "total_received": len(self.received_signals),
            "secret_configured": bool(settings.TRADINGVIEW_WEBHOOK_SECRET),
            "last_signals": self.received_signals[:10]
        }


tradingview_webhook = TradingViewWebhook()
