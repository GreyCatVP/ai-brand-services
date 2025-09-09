import json
from pathlib import Path

CATALOG_PATH = Path("shop_data/catalog.json")

class ShopModule:
    def get_catalog(self) -> str:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            items = json.load(f)
        lines = [f"📦 {p['name']} — {p['price']}₽" for p in items]
        return "\n".join(lines)

    def add_to_cart(self, user_id: int, product_id: str):
        # in-memory cart (Redis-free 30 МБ)
        pass
