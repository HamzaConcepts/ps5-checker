"""
Configuration manager for PlayStation 5 Stock Bot.
Loads settings from .env file or environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from workspace root if it exists
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Config:
    # Target Product Settings
    TARGET_URL = os.getenv(
        "TARGET_URL",
        "https://direct.playstation.com/en-us/buy-consoles/playstation5-pro-console-2-tb"
    )
    PRODUCT_CODE = os.getenv("PRODUCT_CODE", "1000050928")
    PRODUCT_NAME = os.getenv("PRODUCT_NAME", "PlayStation®5 Pro Console - 2 TB")
    
    # Reference Product for testing (In Stock product)
    TEST_PRODUCT_URL = os.getenv(
        "TEST_PRODUCT_URL",
        "https://direct.playstation.com/en-us/buy-consoles/playstation5-digital-edition-console-825-gb"
    )
    TEST_PRODUCT_CODE = os.getenv("TEST_PRODUCT_CODE", "1000049898")
    
    # Monitoring Frequency
    CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
    REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    
    # Discord Notification Settings
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    DISCORD_NOTIFY_ROLE_ID = os.getenv("DISCORD_NOTIFY_ROLE_ID", "").strip()  # e.g., role ID or 'everyone'
    DISCORD_BOT_USERNAME = os.getenv("DISCORD_BOT_USERNAME", "PS5 Stock Alert Bot")
    DISCORD_BOT_AVATAR_URL = os.getenv(
        "DISCORD_BOT_AVATAR_URL",
        "https://media.direct.playstation.com/is/image/sierialto/favicon?fmt=png-alpha"
    )

    # Telegram Notification Settings (Optional)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    # ntfy.sh Push Notification (Optional, 100% Free Instant Mobile Push)
    NTFY_TOPIC = os.getenv("NTFY_TOPIC", "").strip()

    # Audio & Desktop Notification Settings
    ENABLE_DESKTOP_SOUND = os.getenv("ENABLE_DESKTOP_SOUND", "true").lower() in ("true", "1", "yes")
    
    # State Persistence
    STATE_FILE = Path(__file__).resolve().parent / "stock_state.json"
    
    # Cooldown between repeat notifications when product remains in stock (in minutes)
    IN_STOCK_ALERT_COOLDOWN_MINUTES = int(os.getenv("IN_STOCK_ALERT_COOLDOWN_MINUTES", "30"))

    # OCC Commerce API Endpoint
    API_BASE_URL = "https://api.direct.playstation.com/commercewebservices/ps-direct-us/products/productList"
