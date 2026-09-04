"""
State Manager for Stock Bot.
Tracks stock changes, prevents notification spam, and handles alert cooldowns.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from config import Config
from checker import StockResult

logger = logging.getLogger("StateManager")


class StateManager:
    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = state_file or Config.STATE_FILE
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state file {self.state_file}: {e}")
        return {
            "last_status": "unknown",
            "is_in_stock": False,
            "last_check_time": None,
            "last_notified_time": None,
            "checks_count": 0,
            "stock_found_count": 0,
        }

    def _save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save state file: {e}")

    def should_notify(self, result: StockResult, force_notify: bool = False) -> bool:
        """
        Determines whether a notification should be dispatched based on:
        1. Force flag (used during test runs or manual triggers).
        2. Transition from OUT_OF_STOCK -> IN_STOCK.
        3. Product remains IN_STOCK and cooldown window has passed.
        """
        if force_notify:
            return True

        if not result.is_in_stock:
            return False

        # Transition: previously not in stock, now in stock!
        prev_in_stock = self.state.get("is_in_stock", False)
        if not prev_in_stock and result.is_in_stock:
            logger.info("Stock status transitioned from OUT_OF_STOCK to IN_STOCK!")
            return True

        # Check cooldown if still in stock
        last_notified_str = self.state.get("last_notified_time")
        if last_notified_str:
            try:
                last_notified_dt = datetime.fromisoformat(last_notified_str)
                cooldown = timedelta(minutes=Config.IN_STOCK_ALERT_COOLDOWN_MINUTES)
                if datetime.now() - last_notified_dt >= cooldown:
                    logger.info("Cooldown elapsed; sending repeat in-stock reminder.")
                    return True
                else:
                    logger.debug("Product still in stock, but cooldown has not expired yet.")
                    return False
            except Exception:
                return True

        return True

    def record_check(self, result: StockResult, notified: bool = False):
        """
        Updates internal state and persists to disk.
        """
        now_iso = datetime.now().isoformat()
        self.state["last_status"] = result.status_raw
        self.state["is_in_stock"] = result.is_in_stock
        self.state["last_check_time"] = now_iso
        self.state["checks_count"] = self.state.get("checks_count", 0) + 1
        
        if result.is_in_stock:
            self.state["stock_found_count"] = self.state.get("stock_found_count", 0) + 1

        if notified:
            self.state["last_notified_time"] = now_iso

        self._save_state()
