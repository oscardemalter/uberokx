import os
from dotenv import load_dotenv

# Charger .env
load_dotenv()


class Settings:
    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
        self.ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
        self.ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
        self.SECRET_KEY = os.getenv("SECRET_KEY", "")
        self.WEBHOOK_HMAC_SECRET = os.getenv("WEBHOOK_HMAC_SECRET", "")
        self.OKX_OAUTH_CLIENT_ID = os.getenv("OKX_OAUTH_CLIENT_ID", "")
        self.OKX_OAUTH_CLIENT_SECRET = os.getenv("OKX_OAUTH_CLIENT_SECRET", "")
        self.OKX_OAUTH_REDIRECT_URI = os.getenv("OKX_OAUTH_REDIRECT_URI", "https://VOTRE_DOMAINE/api/okx/oauth/callback")
        self.OKX_DEMO = os.getenv("OKX_DEMO", "True").lower() == "true"
        self.TRADING_MODE = os.getenv("TRADING_MODE", "paper")
        self.EXCHANGE_ID = os.getenv("EXCHANGE_ID", "okx")
        self.API_KEY = os.getenv("API_KEY", "")
        self.API_SECRET = os.getenv("API_SECRET", "")
        self.API_PASSPHRASE = os.getenv("API_PASSPHRASE", "")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.MIN_ORDER_USDT = float(os.getenv("MIN_ORDER_USDT", "1.0"))
        self.MAX_DAILY_LOSS_PERCENT = float(os.getenv("MAX_DAILY_LOSS_PERCENT", "5.0"))
        self.MAX_ORDER_NOTIONAL_USDT = float(os.getenv("MAX_ORDER_NOTIONAL_USDT", "1000.0"))
        self.WEBHOOK_SYMBOL_WHITELIST = os.getenv("WEBHOOK_SYMBOL_WHITELIST", "BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT")
        self.PAPER_LEDGER_PATH = os.getenv("PAPER_LEDGER_PATH", "data/paper_ledger.json")
        self.KEYSTORE_PATH = os.getenv("KEYSTORE_PATH", "data/keystore.json")
        self.AUDIT_PATH = os.getenv("AUDIT_PATH", "data/audit.jsonl")
        self.USER_DATA_DIR = os.getenv("USER_DATA_DIR", "user_data")
        self.VERIFICATION_RECORDS_PATH = os.getenv("VERIFICATION_RECORDS_PATH", "verification/tradingview.json")
        self.VERIFICATION_PINE_PATH = os.getenv("VERIFICATION_PINE_PATH", "pine/uberox_emitter_v6.pine")


settings = Settings()


if settings.ENVIRONMENT == "production" and (not settings.SECRET_KEY or not settings.ADMIN_PASSWORD_HASH):
    raise RuntimeError("production: SECRET_KEY et ADMIN_PASSWORD_HASH requis")
