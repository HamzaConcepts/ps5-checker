"""
Notification Dispatcher for PlayStation 5 Stock Bot.
Supports Discord Webhooks (rich embeds), Telegram, ntfy.sh, and local desktop alerts.
"""

import sys
import logging
from datetime import datetime
from typing import Optional
import requests
from config import Config
from checker import StockResult

logger = logging.getLogger("Notifier")


class Notifier:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def send_discord_notification(self, result: StockResult, is_test: bool = False) -> bool:
        """
        Sends a Discord notification with a rich embed to the configured Discord Webhook.
        """
        webhook_url = Config.DISCORD_WEBHOOK_URL
        if not webhook_url:
            logger.info("Discord webhook URL not configured. Skipping Discord notification.")
            return False

        # Mention prefix
        content = ""
        if Config.DISCORD_NOTIFY_ROLE_ID:
            role = Config.DISCORD_NOTIFY_ROLE_ID.strip()
            if role.lower() in ("everyone", "@everyone"):
                content = "@everyone "
            elif role.lower() in ("here", "@here"):
                content = "@here "
            else:
                content = f"<@&{role}> "

        if is_test:
            embed_title = "🧪 [TEST] PS5 Stock Bot Notification Test"
            embed_color = 0x3498DB  # Blue
            status_text = "🟢 In Stock (Test Item)" if result.is_in_stock else "🔴 Out of Stock (Test Item)"
            description = (
                "This is a **test alert** to verify your Discord Webhook configuration.\n"
                f"Notifications are working properly! 🎉"
            )
        else:
            embed_title = "🚨 IN STOCK ALERT: PlayStation®5 Direct! 🚨"
            embed_color = 0x2ECC71  # Vibrant Green
            status_text = "🟢 **IN STOCK - READY TO ORDER!**"
            description = (
                f"**{result.name}** is currently **IN STOCK** on PlayStation Direct!\n\n"
                f"⚡ **Act fast before inventory runs out!**"
            )

        fields = [
            {"name": "📦 Product", "value": result.name, "inline": False},
            {"name": "📊 Status", "value": status_text, "inline": True},
            {"name": "💰 Price", "value": result.price_str or "$899.00", "inline": True},
            {"name": "🏬 Store", "value": "PlayStation Direct (US)", "inline": True},
            {
                "name": "🛒 Direct Purchase Link",
                "value": f"[👉 **Click Here to Open PlayStation Direct**]({result.url})",
                "inline": False,
            },
            {
                "name": "🔍 Verification Method",
                "value": f"`{result.method_used}` (Checked at {result.check_time.strftime('%Y-%m-%d %H:%M:%S')})",
                "inline": False,
            },
        ]

        embed = {
            "title": embed_title,
            "url": result.url,
            "description": description,
            "color": embed_color,
            "fields": fields,
            "thumbnail": {
                "url": "https://media.direct.playstation.com/is/image/sierialto/favicon?fmt=png-alpha"
            },
            "footer": {
                "text": "PS5 Stock Monitor Bot • Free & Open Source",
                "icon_url": "https://media.direct.playstation.com/is/image/sierialto/favicon?fmt=png-alpha",
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        payload = {
            "username": Config.DISCORD_BOT_USERNAME,
            "avatar_url": Config.DISCORD_BOT_AVATAR_URL,
            "content": content if not is_test else f"{content}Bot test message triggered.",
            "embeds": [embed],
        }

        try:
            resp = self.session.post(webhook_url, json=payload, timeout=10)
            if resp.status_code in (200, 204):
                logger.info("✅ Discord notification sent successfully!")
                return True
            else:
                logger.error(f"❌ Discord webhook failed with status {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending Discord webhook: {e}")
            return False

    def send_telegram_notification(self, result: StockResult, is_test: bool = False) -> bool:
        """
        Sends Telegram notification if configured.
        """
        token = Config.TELEGRAM_BOT_TOKEN
        chat_id = Config.TELEGRAM_CHAT_ID
        if not token or not chat_id:
            return False

        header = "🧪 *[TEST]* " if is_test else "🚨 *STOCK ALERT* 🚨\n"
        msg = (
            f"{header}"
            f"*{result.name}* is *IN STOCK*!\n\n"
            f"💰 *Price:* {result.price_str}\n"
            f"🏬 *Store:* PlayStation Direct\n"
            f"🔗 [Buy Now on PlayStation Direct]({result.url})"
        )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            resp = self.session.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": msg,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    def send_ntfy_notification(self, result: StockResult, is_test: bool = False) -> bool:
        """
        Sends instant mobile push notification via ntfy.sh (100% free, no registration needed).
        """
        topic = Config.NTFY_TOPIC
        if not topic:
            return False

        title = f"{'[TEST] ' if is_test else '🚨 '}PS5 IN STOCK: {result.name}"
        headers = {
            "Title": title,
            "Priority": "urgent" if not is_test else "default",
            "Tags": "tada,video_game,moneybag" if not is_test else "test_tube",
            "Click": result.url,
        }
        body = f"Price: {result.price_str}\nStatus: IN STOCK\nClick to buy now: {result.url}"

        try:
            resp = self.session.post(
                f"https://ntfy.sh/{topic}",
                data=body.encode("utf-8"),
                headers=headers,
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Error sending ntfy push notification: {e}")
            return False

    def trigger_audio_alert(self):
        """
        Plays sound on local machine when in stock.
        """
        if not Config.ENABLE_DESKTOP_SOUND:
            return
        try:
            if sys.platform == "win32":
                import winsound
                for _ in range(3):
                    winsound.Beep(1200, 300)
                    winsound.Beep(1800, 400)
            else:
                # Terminal bell
                print("\a\a\a", end="", flush=True)
        except Exception:
            pass

    def notify_all(self, result: StockResult, is_test: bool = False) -> dict:
        """
        Dispatches alerts across all configured channels.
        """
        results = {
            "discord": self.send_discord_notification(result, is_test=is_test),
            "telegram": self.send_telegram_notification(result, is_test=is_test),
            "ntfy": self.send_ntfy_notification(result, is_test=is_test),
        }
        if result.is_in_stock or is_test:
            self.trigger_audio_alert()
        return results
