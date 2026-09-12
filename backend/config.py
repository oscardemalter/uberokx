from pydantic import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "production"
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD_HASH: str = ""
    SECRET_KEY: str = ""
    WEBHOOK_HMAC_SECRET: str = ""
    OKX_OAUTH_CLIENT_ID: str = ""
    OKX_OAUTH_CLIENT_SECRET: str = ""
    OKX_OAUTH_REDIRECT_URI: str = "https://VOTRE_DOMAINE/api/okx/oauth/callback"
    OKX_DEMO: bool = True
    TRADING_MODE: str = "paper"
    EXCHANGE_ID: str = "okx"
    API_KEY: str = ""
    API_SECRET: str = ""
    API_PASSPHRASE: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    MIN_ORDER_USDT: float = 1.0
    MAX_DAILY_LOSS_PERCENT: float = 5.0
    MAX_ORDER_NOTIONAL_USDT: float = 1000.0
    WEBHOOK_SYMBOL_WHITELIST: str = "BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT"
    PAPER_LEDGER_PATH: str = "data/paper_ledger.json"
    KEYSTORE_PATH: str = "data/keystore.json"
    AUDIT_PATH: str = "data/audit.jsonl"
    USER_DATA_DIR: str = "user_data"
    VERIFICATION_RECORDS_PATH: str = "verification/tradingview.json"
    VERIFICATION_PINE_PATH: str = "pine/uberox_emitter_v6.pine"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


if settings.ENVIRONMENT == "production" and (not settings.SECRET_KEY or not settings.ADMIN_PASSWORD_HASH):
    raise RuntimeError("production: SECRET_KEY et ADMIN_PASSWORD_HASH requis")
