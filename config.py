# config.py
import os

# Bot token (set via environment variable or directly here)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8017553859:AAHacxJhRk97GtKI8rNhjoXht_xh77kwiiQ")

# Channels required for verification (bot must be admin in these)
REQUIRED_CHANNELS = [
    '@shadowsquad0',
    '@Originlabs',
    '@ShadowsquadHits',
    '@Binhub_Originlabs'
]

# Notification channel
NOTIFICATION_CHANNEL = '@shadowsquad0'

# Default owner IDs (replace with actual Telegram user IDs)
DEFAULT_OWNERS = [7436974867, 7218606355, 5933410316, 5822279535]
