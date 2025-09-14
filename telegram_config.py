"""
Telegram Bot Configuration
"""
import os
from typing import Dict, Optional

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Phone number to Telegram chat ID mapping
# Add your member phone numbers and their corresponding Telegram chat IDs here
PHONE_TO_TELEGRAM_MAPPING: Dict[str, str] = {
    "+491234567890": "123456789",  # Max Mustermann
    "+499876543210": "987654321",  # Erika Beispiel
    "+491112223334": "111222333",  # Anna Schmidt
    "+499998887776": "999888777",  # Tom Weber
}

def get_telegram_chat_id(phone_number: str) -> Optional[str]:
    """Get Telegram chat ID for a phone number"""
    return PHONE_TO_TELEGRAM_MAPPING.get(phone_number)

def is_telegram_configured() -> bool:
    """Check if Telegram bot is properly configured"""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
