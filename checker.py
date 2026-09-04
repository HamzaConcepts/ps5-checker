"""
Stock Checker Engine for PlayStation Direct.
Implements dual-mode verification:
1. High-speed Direct Commerce OCC REST API
2. Full HTML Scraper Fallback
"""

import re
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import requests
from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PS5Checker")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]


@dataclass
class StockResult:
    product_code: str
    name: str
    is_in_stock: bool
    status_raw: str
    price_str: str
    price_val: Optional[float]
    url: str
    image_url: Optional[str]
    check_time: datetime
    method_used: str
    error: Optional[str] = None


class PlayStationChecker:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def _get_headers(self, is_api: bool = True) -> dict:
        ua = random.choice(USER_AGENTS)
        headers = {
            "User-Agent": ua,
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        if is_api:
            headers.update({
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://direct.playstation.com",
                "Referer": "https://direct.playstation.com/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            })
        else:
            headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            })
        return headers

    def check_product_api(self, product_code: str, product_url: str) -> Optional[StockResult]:
        """
        Check stock status using PlayStation Direct Commerce OCC REST API.
        """
        api_url = f"https://api.direct.playstation.com/commercewebservices/ps-direct-us/products/productList?fields=BASIC&productCodes={product_code}"
        try:
            resp = self.session.get(
                api_url,
                headers=self._get_headers(is_api=True),
                timeout=Config.REQUEST_TIMEOUT_SECONDS,
            )
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("products", [])
                if products:
                    prod = products[0]
                    name = prod.get("name", Config.PRODUCT_NAME)
                    stock_obj = prod.get("stock", {})
                    status_raw = stock_obj.get("stockLevelStatus", "unknown")
                    is_low_stock = stock_obj.get("isProductLowStock", False)
                    
                    # inStock or lowStock indicates purchasable stock
                    is_in_stock = status_raw.lower() in ("instock", "in_stock") or is_low_stock
                    
                    price_info = prod.get("price", {})
                    price_val = price_info.get("value")
                    price_symbol = price_info.get("currencySymbol", "$")
                    base_price = price_info.get("basePrice", "")
                    decimal_price = price_info.get("decimalPrice", "00")
                    
                    if price_val:
                        price_str = f"{price_symbol}{price_val:.2f}"
                    elif base_price:
                        price_str = f"{price_symbol}{base_price}.{decimal_price}"
                    else:
                        price_str = "See Price at PS Direct"

                    # Extract image URL if available
                    image_url = None
                    images = prod.get("images", [])
                    for img in images:
                        if img.get("format") in ("product", "zoom", "thumbnail") or not image_url:
                            image_url = img.get("url")

                    return StockResult(
                        product_code=product_code,
                        name=name,
                        is_in_stock=is_in_stock,
                        status_raw=status_raw,
                        price_str=price_str,
                        price_val=price_val,
                        url=product_url,
                        image_url=image_url,
                        check_time=datetime.now(),
                        method_used="API_PRODUCT_LIST",
                    )
        except Exception as e:
            logger.warning(f"Product list API check failed for {product_code}: {e}")

        # Fallback to single product detail endpoint
        detail_url = f"https://api.direct.playstation.com/commercewebservices/ps-direct-us/products/{product_code}"
        try:
            resp = self.session.get(
                detail_url,
                headers=self._get_headers(is_api=True),
                timeout=Config.REQUEST_TIMEOUT_SECONDS,
            )
            if resp.status_code == 200:
                prod = resp.json()
                name = prod.get("name", Config.PRODUCT_NAME)
                stock_obj = prod.get("stock", {})
                status_raw = stock_obj.get("stockLevelStatus", "unknown")
                is_in_stock = status_raw.lower() in ("instock", "in_stock")
                
                price_info = prod.get("price", {})
                price_str = price_info.get("formattedValue", f"${price_info.get('value', 'N/A')}")
                price_val = price_info.get("value")

                return StockResult(
                    product_code=product_code,
                    name=name,
                    is_in_stock=is_in_stock,
                    status_raw=status_raw,
                    price_str=price_str,
                    price_val=price_val,
                    url=product_url,
                    image_url=None,
                    check_time=datetime.now(),
                    method_used="API_DETAIL",
                )
        except Exception as e:
            logger.warning(f"Product detail API check failed for {product_code}: {e}")

        return None

    def check_product_html(self, product_code: str, product_url: str) -> StockResult:
        """
        HTML Webpage scraper fallback.
        """
        try:
            resp = self.session.get(
                product_url,
                headers=self._get_headers(is_api=False),
                timeout=Config.REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            html = resp.text

            # Check for title/name
            title_match = re.search(r'<title>(.*?)</title>', html, re.I)
            name = title_match.group(1).split('|')[0].strip() if title_match else Config.PRODUCT_NAME

            # Check stock indicators in HTML
            is_unavailable = bool(re.search(r'(Currently Unavailable|Out of Stock|Sold Out)', html, re.I))
            has_add_to_cart = bool(re.search(r'data-product-code=["\']' + re.escape(product_code) + r'["\'][^>]*aria-label=["\']Add to Cart["\']', html, re.I))

            # If add to cart is present and not explicitly unavailable
            is_in_stock = has_add_to_cart and not is_unavailable
            status_raw = "inStock" if is_in_stock else "outOfStock"

            return StockResult(
                product_code=product_code,
                name=name,
                is_in_stock=is_in_stock,
                status_raw=status_raw,
                price_str="See Website",
                price_val=None,
                url=product_url,
                image_url=None,
                check_time=datetime.now(),
                method_used="HTML_SCRAPER",
            )
        except Exception as e:
            logger.error(f"HTML scraper check failed for {product_url}: {e}")
            return StockResult(
                product_code=product_code,
                name=Config.PRODUCT_NAME,
                is_in_stock=False,
                status_raw="error",
                price_str="Unknown",
                price_val=None,
                url=product_url,
                image_url=None,
                check_time=datetime.now(),
                method_used="FAILED",
                error=str(e),
            )

    def check(self, product_code: str = None, product_url: str = None) -> StockResult:
        """
        Executes primary API check with automatic fallback to HTML scraper.
        """
        code = product_code or Config.PRODUCT_CODE
        url = product_url or Config.TARGET_URL

        # Primary: High-speed API
        result = self.check_product_api(code, url)
        if result:
            return result

        # Fallback: HTML Scraper
        logger.info("Falling back to HTML scraper...")
        return self.check_product_html(code, url)
