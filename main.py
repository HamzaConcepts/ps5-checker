"""
Main entry point for PlayStation 5 Stock Monitoring Bot.
"""

import sys
import time
import argparse
import logging
from datetime import datetime
from colorama import init, Fore, Style

from config import Config
from checker import PlayStationChecker, StockResult
from state_manager import StateManager
from notifier import Notifier

# Ensure standard streams use UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Initialize colorama
init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format=f"{Fore.CYAN}%(asctime)s{Style.RESET_ALL} [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PS5StockBot")


def print_banner():
    banner = f"""
{Fore.BLUE}+--------------------------------------------------------------+
|               * PLAYSTATION 5 STOCK MONITOR *                |
|                 Free, Real-Time Stock Checker                |
+--------------------------------------------------------------+{Style.RESET_ALL}
    """
    print(banner)


def check_and_notify(
    checker: PlayStationChecker,
    state_mgr: StateManager,
    notifier: Notifier,
    product_code: str = None,
    product_url: str = None,
    force_notify: bool = False,
    is_test: bool = False,
) -> StockResult:
    """
    Performs a single check and dispatches notifications if state warrants.
    """
    code = product_code or Config.PRODUCT_CODE
    url = product_url or Config.TARGET_URL

    result = checker.check(product_code=code, product_url=url)

    status_color = Fore.GREEN if result.is_in_stock else Fore.RED
    status_label = "IN STOCK 🟢" if result.is_in_stock else "OUT OF STOCK 🔴"

    print(f"\n{Fore.LIGHTBLACK_EX}─────────────────────────────────────────────────────────────{Style.RESET_ALL}")
    print(f"📦 Product:    {Fore.WHITE}{Style.BRIGHT}{result.name}{Style.RESET_ALL}")
    print(f"📊 Status:     {status_color}{Style.BRIGHT}{status_label}{Style.RESET_ALL} (Raw: {result.status_raw})")
    print(f"💰 Price:      {Fore.YELLOW}{result.price_str}{Style.RESET_ALL}")
    print(f"🔍 Method:     {Fore.MAGENTA}{result.method_used}{Style.RESET_ALL}")
    print(f"🔗 Link:       {Fore.BLUE}{result.url}{Style.RESET_ALL}")
    print(f"⏰ Timestamp:  {Fore.LIGHTBLACK_EX}{result.check_time.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}─────────────────────────────────────────────────────────────{Style.RESET_ALL}\n")

    should_send = state_mgr.should_notify(result, force_notify=force_notify or is_test)
    if should_send:
        print(f"{Fore.GREEN}{Style.BRIGHT}📢 Dispatching notifications...{Style.RESET_ALL}")
        notif_results = notifier.notify_all(result, is_test=is_test)
        for channel, success in notif_results.items():
            if success:
                print(f"  {Fore.GREEN}✓ {channel.capitalize()}: Sent successfully{Style.RESET_ALL}")
            elif channel == "discord" and not Config.DISCORD_WEBHOOK_URL:
                print(f"  {Fore.YELLOW}ℹ Discord: Not configured in .env (Add DISCORD_WEBHOOK_URL to enable){Style.RESET_ALL}")
        state_mgr.record_check(result, notified=True)
    else:
        state_mgr.record_check(result, notified=False)

    return result


def run_test_mode(checker: PlayStationChecker, state_mgr: StateManager, notifier: Notifier):
    """
    Executes a test verification run against:
    1. The in-stock reference item (PS5 Digital) to confirm in-stock detection.
    2. The target item (PS5 Pro) to confirm out-of-stock detection.
    3. Sends a test notification to Discord / other channels.
    """
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}=== RUNNING BOT VERIFICATION & TEST SUITE ==={Style.RESET_ALL}\n")

    print(f"{Fore.CYAN}[Test 1/2] Checking known In-Stock Reference (PS5 Digital)...{Style.RESET_ALL}")
    in_stock_res = checker.check(
        product_code=Config.TEST_PRODUCT_CODE,
        product_url=Config.TEST_PRODUCT_URL,
    )
    if in_stock_res.is_in_stock:
        print(f"{Fore.GREEN}✓ In-Stock detection verified! ({in_stock_res.name}: {in_stock_res.price_str}){Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠ Reference item returned status: {in_stock_res.status_raw}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}[Test 2/2] Checking Target Item (PS5 Pro Console)...{Style.RESET_ALL}")
    pro_res = checker.check(
        product_code=Config.PRODUCT_CODE,
        product_url=Config.TARGET_URL,
    )
    print(f"{Fore.BLUE}✓ Target Item Status: {pro_res.status_raw} (Purchasable: {pro_res.is_in_stock}){Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}[Notification Test] Sending sample Discord test alert...{Style.RESET_ALL}")
    check_and_notify(
        checker,
        state_mgr,
        notifier,
        product_code=Config.TEST_PRODUCT_CODE,
        product_url=Config.TEST_PRODUCT_URL,
        force_notify=True,
        is_test=True,
    )
    print(f"\n{Fore.GREEN}{Style.BRIGHT}=== TEST COMPLETE ==={Style.RESET_ALL}\n")


def run_continuous_loop(
    checker: PlayStationChecker,
    state_mgr: StateManager,
    notifier: Notifier,
    interval_seconds: int,
):
    print(f"{Fore.GREEN}Starting continuous monitoring loop (Interval: {interval_seconds}s)...{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}Press Ctrl+C to stop the bot at any time.{Style.RESET_ALL}\n")

    check_num = 1
    try:
        while True:
            print(f"{Fore.CYAN}--- Check #{check_num} at {datetime.now().strftime('%H:%M:%S')} ---{Style.RESET_ALL}")
            check_and_notify(checker, state_mgr, notifier)
            check_num += 1
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Monitoring stopped by user. Goodbye!{Style.RESET_ALL}")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="PlayStation 5 Direct Stock Checker Bot")
    parser.add_argument("--once", action="store_true", help="Run a single check and exit (ideal for GitHub Actions / Cron)")
    parser.add_argument("--test", action="store_true", help="Run verification test suite and send a test Discord notification")
    parser.add_argument("--interval", type=int, default=Config.CHECK_INTERVAL_SECONDS, help="Check interval in seconds (default: 60)")

    args = parser.parse_args()

    print_banner()

    checker = PlayStationChecker()
    state_mgr = StateManager()
    notifier = Notifier()

    if args.test:
        run_test_mode(checker, state_mgr, notifier)
    elif args.once:
        logger.info("Executing single stock check (--once mode)...")
        check_and_notify(checker, state_mgr, notifier)
    else:
        run_continuous_loop(checker, state_mgr, notifier, interval_seconds=args.interval)


if __name__ == "__main__":
    main()
