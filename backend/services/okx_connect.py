import base64, hashlib, hmac, json, os, re, time, datetime
from urllib.parse import urlparse, urlencode
import httpx
from cryptography.fernet import Fernet
from backend.config import settings
OKX_REST = "https://www.okx.com"
ADDR_RE = {"evm": re.compile(r"^0x[a-fA-F0-9]{40}$"),
           "solana": re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$"),
           "bitcoin": re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$"),
           "tron": re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")}
def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
class OkxConnect:
    def __init__(self):
        self._fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest()))
        self._store = self._load(); self.audit = []
    def _load(self):
        try:
            if os.path.exists(settings.KEYSTORE_PATH):
                with open(settings.KEYSTORE_PATH, "rb") as fh:
                    return json.loads(self._fernet.decrypt(fh.read()).decode())
        except Exception:
            pass
        return {"keys": None, "oauth": None, "signalbot": None, "wallet": None}
    def _save(self):
        os.makedirs(os.path.dirname(settings.KEYSTORE_PATH) or ".", exist_ok=True)
        with open(settings.KEYSTORE_PATH, "wb") as fh:
            fh.write(self._fernet.encrypt(json.dumps(self._store).encode()))
        try: os.chmod(settings.KEYSTORE_PATH, 0o600)
        except Exception: pass
    def _log(self, ev, detail=""):
        self.audit.insert(0, {"ts": _utcnow(), "event": ev, "detail": detail}); del self.audit[300:]
    def _keys(self):
        k = self._store.get("keys") or {}
        return k.get("key",""), k.get("secret",""), k.get("passphrase","")
    def _headers(self, method, path, body=""):
        k, s, p = self._keys()
        ts = datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        msg = ts + method + path + body
        sign = base64.b64encode(hmac.new(s.encode(), msg.encode(), hashlib.sha256).digest()).decode()
        h = {"OK-ACCESS-KEY": k, "OK-ACCESS-SIGN": sign, "OK-ACCESS-TIMESTAMP": ts,
             "OK-ACCESS-PASSPHRASE": p, "Content-Type": "application/json"}
        if settings.OKX_DEMO: h["x-simulated-trading"] = "1"
        return h
    async def verify_keys(self):
        k, s, _ = self._keys()
        if not (k and s): return {"success": False, "reason": "cles absentes"}
        t0 = time.time()
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(OKX_REST + "/api/v5/account/balance", headers=self._headers("GET", "/api/v5/account/balance"))
        d = r.json(); ok = d.get("code") == "0"
        self._log("KEYS_VERIFY", "ok" if ok else d.get("msg",""))
        return {"success": ok, "latency_ms": int((time.time()-t0)*1000), "msg": d.get("msg","")}
    async def set_keys(self, key, secret, passphrase):
        if not (key and secret and passphrase): return {"success": False, "reason": "key/secret/passphrase requis"}
        self._store["keys"] = {"key": key, "secret": secret, "passphrase": passphrase}; self._save()
        res = await self.verify_keys()
        if not res["success"]: self._store["keys"] = None; self._save()
        return res
    async def fast_connect(self, key, secret, passphrase, demo=True):
        settings.OKX_DEMO = bool(demo)
        res = await self.set_keys(key, secret, passphrase)
        if res.get("success"): res["method"] = "fast_connect"; self._log("FAST_CONNECT", "demo="+str(settings.OKX_DEMO))
        return res
    def oauth_start(self, state):
        if not (settings.OKX_OAUTH_CLIENT_ID and settings.OKX_OAUTH_CLIENT_SECRET):
            return {"success": False, "reason": "OAuth non configure (app OKX eligible requise). Repli : cles API."}
        url = OKX_REST + "/oauth2/authorize?" + urlencode({"client_id": settings.OKX_OAUTH_CLIENT_ID,
            "response_type": "code", "redirect_uri": settings.OKX_OAUTH_REDIRECT_URI, "state": state})
        return {"success": True, "url": url}
    async def oauth_callback(self, code, state):
        if not code: return {"success": False, "reason": "code manquant"}
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(OKX_REST + "/oauth2/token", data={"grant_type":"authorization_code","code":code,
                "client_id": settings.OKX_OAUTH_CLIENT_ID, "client_secret": settings.OKX_OAUTH_CLIENT_SECRET,
                "redirect_uri": settings.OKX_OAUTH_REDIRECT_URI})
        d = r.json()
        if "access_token" not in d:
            return {"success": False, "reason": "Token refuse par OKX.", "detail": d}
        self._store["oauth"] = {"access": d["access_token"], "refresh": d.get("refresh_token",""),
                                "exp": int(time.time()) + int(d.get("expires_in", 3600))}
        self._save(); self._log("OAUTH_OK")
        return {"success": True, "method": "oauth"}
    def set_signalbot(self, url, secret):
        p = urlparse(url)
        if p.scheme != "https" or not p.hostname or not p.hostname.endswith("okx.com"):
            return {"success": False, "reason": "URL webhook OKX https invalide"}
        if not secret: return {"success": False, "reason": "secret Signal Bot requis"}
        self._store["signalbot"] = {"url": url, "secret": secret}; self._save(); self._log("SIGNALBOT_LINKED", p.hostname or "")
        return {"success": True, "method": "signalbot"}
    async def push_signal(self, sig):
        sb = self._store.get("signalbot")
        if not sb: return {"success": False, "reason": "Signal Bot non lie"}
        body = json.dumps({"symbol": sig["symbol"], "action": sig["action"], "price": sig["price"],
                           "qty": sig.get("qty",0), "time_ms": sig["time_ms"], "nonce": sig["nonce"],
                           "sign": hmac.new(sb["secret"].encode(), sig["nonce"].encode(), hashlib.sha256).hexdigest()},
                          separators=(",",":"))
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(sb["url"], content=body, headers={"Content-Type":"application/json",
                "X-UBX-Signature": hmac.new(sb["secret"].encode(), body.encode(), hashlib.sha256).hexdigest()})
        self._log("SIGNAL_PUSH", sig["symbol"] + " http=" + str(r.status_code))
        return {"success": 200 <= r.status_code < 300, "http": r.status_code}
    def set_wallet(self, address, chain):
        rx = ADDR_RE.get(chain)
        if not rx or not rx.match(address or ""): return {"success": False, "reason": "adresse " + chain + " invalide"}
        self._store["wallet"] = {"address": address, "chain": chain}; self._save(); self._log("WALLET_LINKED", chain)
        return {"success": True, "method": "wallet",
                "note": "Adresse publique seule. Signature et execution DEX dans l'app OKX Wallet."}
    async def dex_quote(self, chain_id, tok_from, tok_to, amount):
        if not self._store.get("wallet"): return {"success": False, "reason": "wallet non lie"}
        params = {"chainId": chain_id, "fromTokenAddress": tok_from, "toTokenAddress": tok_to, "amount": amount}
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(OKX_REST + "/api/v5/dex/aggregator/quote", params=params)
        d = r.json()
        return {"success": d.get("code") == "0", "quote": d.get("data"),
                "note": "Execution = signature utilisateur dans OKX Wallet."}
    def can_trade(self):
        k, s, _ = self._keys(); o = self._store.get("oauth") or {}
        return bool(k and s) or bool(o.get("exp", 0) > time.time())
    def ccxt_config(self):
        k, s, p = self._keys()
        cfg = {"enableRateLimit": True, "options": {"defaultType": "swap"}}
        if k and s: cfg.update({"apiKey": k, "secret": s, "password": p})
        if settings.OKX_DEMO: cfg["headers"] = {"x-simulated-trading": "1"}
        return cfg
    def status(self):
        o = self._store.get("oauth") or {}
        return {"keys_api": bool(self._store.get("keys")), "oauth": bool(o.get("exp",0) > time.time()),
                "signalbot": bool(self._store.get("signalbot")), "wallet": bool(self._store.get("wallet")),
                "demo": settings.OKX_DEMO, "can_trade": self.can_trade(), "audit": self.audit[:10]}
okx_connect = OkxConnect()
