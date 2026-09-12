"""
Configuration settings for UberOKX platform.
Loads environment variables from .env file.
"""

import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings from environment variables with validation."""
    
    def __init__(self):
        # Environment
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
        if self.ENVIRONMENT not in ("development", "staging", "production"):
            raise ValueError(f"Invalid ENVIRONMENT: {self.ENVIRONMENT}")
        
        # Authentication
        self.ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip()
        self.ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
        self.SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
        
        # Webhook security
        self.WEBHOOK_HMAC_SECRET = os.getenv("WEBHOOK_HMAC_SECRET", "").strip()
        
        # OKX OAuth
        self.OKX_OAUTH_CLIENT_ID = os.getenv("OKX_OAUTH_CLIENT_ID", "").strip()
        self.OKX_OAUTH_CLIENT_SECRET = os.getenv("OKX_OAUTH_CLIENT_SECRET", "").strip()
        self.OKX_OAUTH_REDIRECT_URI = os.getenv(
            "OKX_OAUTH_REDIRECT_URI",
            "https://VOTRE_DOMAINE/api/okx/oauth/callback"
        ).strip()
        
        # OKX Settings
        self.OKX_DEMO = os.getenv("OKX_DEMO", "True").lower() == "true"
        self.TRADING_MODE = os.getenv("TRADING_MODE", "paper").lower()
        if self.TRADING_MODE not in ("paper", "live"):
            raise ValueError(f"Invalid TRADING_MODE: {self.TRADING_MODE}")
        
        # Exchange
        self.EXCHANGE_ID = os.getenv("EXCHANGE_ID", "okx").lower()
        self.API_KEY = os.getenv("API_KEY", "").strip()
        self.API_SECRET = os.getenv("API_SECRET", "").strip()
        self.API_PASSPHRASE = os.getenv("API_PASSPHRASE", "").strip()
        
        # LLM
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
        self.LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
        
        # Risk Management
        min_order = float(os.getenv("MIN_ORDER_USDT", "1.0"))
        if min_order <= 0:
            raise ValueError("MIN_ORDER_USDT must be positive")
        self.MIN_ORDER_USDT = min_order
        
        max_daily_loss = float(os.getenv("MAX_DAILY_LOSS_PERCENT", "5.0"))
        if max_daily_loss <= 0 or max_daily_loss > 100:
            raise ValueError("MAX_DAILY_LOSS_PERCENT must be between 0 and 100")
        self.MAX_DAILY_LOSS_PERCENT = max_daily_loss
        
        max_notional = float(os.getenv("MAX_ORDER_NOTIONAL_USDT", "1000.0"))
        if max_notional <= 0:
            raise ValueError("MAX_ORDER_NOTIONAL_USDT must be positive")
        self.MAX_ORDER_NOTIONAL_USDT = max_notional
        
        # Webhook whitelist
        self.WEBHOOK_SYMBOL_WHITELIST = os.getenv(
            "WEBHOOK_SYMBOL_WHITELIST",
            "BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT"
        ).strip()
        
        # Data paths
        self.PAPER_LEDGER_PATH = os.getenv("PAPER_LEDGER_PATH", "data/paper_ledger.json").strip()
        self.KEYSTORE_PATH = os.getenv("KEYSTORE_PATH", "data/keystore.json").strip()
        self.AUDIT_PATH = os.getenv("AUDIT_PATH", "data/audit.jsonl").strip()
        self.USER_DATA_DIR = os.getenv("USER_DATA_DIR", "user_data").strip()
        
        # Verification paths
        self.VERIFICATION_RECORDS_PATH = os.getenv(
            "VERIFICATION_RECORDS_PATH",
            "verification/tradingview.json"
        ).strip()
        self.VERIFICATION_PINE_PATH = os.getenv(
            "VERIFICATION_PINE_PATH",
            "pine/uberox_emitter_v6.pine"
        ).strip()


settings = Settings()


# Validate critical settings for production
if settings.ENVIRONMENT == "production":
    if not settings.SECRET_KEY:
        raise RuntimeError("production: SECRET_KEY requis dans .env")
    if not settings.ADMIN_PASSWORD_HASH:
        raise RuntimeError("production: ADMIN_PASSWORD_HASH requis dans .env")
    if not settings.WEBHOOK_HMAC_SECRET:
        raise RuntimeError("production: WEBHOOK_HMAC_SECRET requis dans .env")
