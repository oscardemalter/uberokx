import json, os, subprocess, sys, time
from pathlib import Path
from backend.config import settings
from backend.services.okx_connect import okx_connect
from backend.services.exchange import exchange_service
STRATEGY_NAME = "UberOKXMojoStrategy"
def ft_available():
    import importlib.util
    return importlib.util.find_spec("freqtrade") is not None
class FreqTradeBridge:
    def __init__(self):
        self.user_data = Path(settings.USER_DATA_DIR).resolve()
        self.base = self.user_data.parent
        self.config_path = self.user_data / "config_uberox.json"
        self.pid_file = self.user_data / "bridge.pid"
        self.log_path = self.user_data / "logs" / "uberox_bridge.log"
    def _running_pid(self):
        if not self.pid_file.is_file(): return None
        pid = int(self.pid_file.read_text().strip() or 0)
        if not pid: return None
        try:
            os.kill(pid, 0); return pid
        except OSError:
            return None
    def _config(self, dry_run):
        c = okx_connect.ccxt_config()
        return {"bot_name":"uberox_mojo_bridge","max_open_trades":3,"stake_currency":"USDT",
                "stake_amount":1.0,"dry_run":dry_run,"dry_run_wallet":10000,"timeframe":"5m",
                "trading_mode":"spot","margin_mode":"",
                "unfilledtimeout":{"entry":10,"exit":10,"unit":"minutes"},
                "exchange":{"name":"okx","key":c.get("apiKey",""),"secret":c.get("secret",""),
                            "password":c.get("password",""),"ccxt_config":{},"ccxt_async_config":{},
                            "pair_whitelist":["BTC/USDT","ETH/USDT","SOL/USDT"],"pair_blacklist":[]},
                "entry_pricing":{"price_side":"same","use_order_book":True,"order_book_top":1},
                "exit_pricing":{"price_side":"same","use_order_book":True,"order_book_top":1},
                "initial_state":"running","internals":{"process_throttle_secs":5}}
    def start(self, confirm_live=False):
        if not ft_available(): return {"success": False, "reason": "freqtrade non installe"}
        if self._running_pid(): return {"success": False, "reason": "bridge deja demarre"}
        mode = settings.TRADING_MODE; dry = mode != "live"
        if mode == "live":
            if exchange_service.killed or not okx_connect.can_trade():
                return {"success": False, "reason": "LIVE refuse : kill-switch ou cles."}
            if not confirm_live: return {"success": False, "reason": "LIVE refuse : confirmation."}
        strat = self.user_data / "strategies" / (STRATEGY_NAME + ".py")
        if not strat.is_file(): return {"success": False, "reason": "strategie absente"}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self._config(dry), indent=2), encoding="utf-8")
        try: os.chmod(self.config_path, 0o600)
        except Exception: pass
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        logf = open(self.log_path, "ab")
        p = subprocess.Popen([sys.executable, "-m", "freqtrade", "trade", "--config",
                              str(self.config_path), "--strategy", STRATEGY_NAME],
                             stdout=logf, stderr=subprocess.STDOUT, cwd=str(self.base))
        self.pid_file.write_text(str(p.pid))
        return {"success": True, "pid": p.pid, "mode": mode, "dry_run": dry}
    def stop(self):
        pid = self._running_pid()
        if not pid: return {"success": False, "reason": "bridge non demarre"}
        try:
            os.kill(pid, 15); time.sleep(1.0)
        except OSError:
            pass
        self.pid_file.unlink(missing_ok=True)
        return {"success": True, "stopped_pid": pid}
    def status(self):
        pid = self._running_pid(); tail = []
        if self.log_path.is_file():
            tail = self.log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-10:]
        return {"running": bool(pid), "pid": pid, "freqtrade_installed": ft_available(),
                "mode": settings.TRADING_MODE, "log_tail": tail}
    def backtest(self, days=30):
        if not ft_available(): return {"success": False, "reason": "freqtrade non installe"}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self._config(True), indent=2), encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "freqtrade", "backtesting", "--config",
                            str(self.config_path), "--strategy", STRATEGY_NAME, "--timerange",
                            str(int(time.time())-days*86400) + "-" + str(int(time.time()))],
                           cwd=str(self.base), capture_output=True, text=True, timeout=600)
        out = (r.stdout or "") + (r.stderr or "")
        return {"success": r.returncode == 0, "output_tail": out.splitlines()[-40:],
                "note": "backtest = observation simulee, pas une preuve de profit futur"}
ft_bridge = FreqTradeBridge()
