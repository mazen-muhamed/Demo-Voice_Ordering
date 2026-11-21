import json
import os
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

@dataclass(frozen=True)
class MenuItem:
    id: int
    name: str
    price: Decimal
    aliases: tuple[str, ...] = ()
    variants: dict[str, float] | None = None  # from menu_items.variants JSONB


class MenuProvider(Protocol):
    def get(self, item_id: int) -> MenuItem | None: ...
    def find(self, text: str) -> MenuItem | None: ...
    def all(self) -> list[MenuItem]: ...


_DIACRITICS = re.compile(r"[\u064B-\u0652\u0640]")


def normalize(text: str) -> str:
    t = _DIACRITICS.sub("", text.strip().lower())
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


_SEED = [
    (1, "كشري", "35", ("كوشري", "طبق كشري")),
    (2, "فول", "15", ("طبق فول", "فول مدمس")),
    (3, "طعمية", "12", ("فلافل", "طعميه")),
    (4, "فراخ مشوية", "120", ("فرخة", "فراخ", "نص فرخة")),
    (5, "كبدة", "70", ("كبده", "كبدة اسكندراني")),
    (6, "كولا", "20", ("كوكاكولا", "كوكا", "كوكاكولا")),
    (7, "بيبسي", "20", ("بيبسى",)),
    (8, "مياه", "8", ("ماية", "مايه", "ميه", "مياه معدنية")),
    (9, "سلطة", "15", ("سلطه", "سلطة خضرا", "سلطة خضراء")),
    (10, "أرز", "15", ("رز", "ارز", "طبق رز")),
    (11, "ملوخية", "40", ("ملوخيه", "ملوخية بالفراخ")),
    (12, "بطاطس", "25", ("بطاطا", "بطاطس محمرة", "فرايز")),
]

class InMemoryMenu:
    def __init__(self) -> None:
        self._items = {
            i: MenuItem(i, n, Decimal(p), tuple(al)) for i, n, p, al in _SEED
        }
        self._index: dict[str, MenuItem] = {}
        for it in self._items.values():
            for key in (it.name, *it.aliases):
                self._index[normalize(key)] = it

    def get(self, item_id: int) -> MenuItem | None:
        return self._items.get(item_id)

    def find(self, text: str) -> MenuItem | None:
        return self._index.get(normalize(text))

    def all(self) -> list[MenuItem]:
        return list(self._items.values())


class SqlMenu:
    def __init__(self, dsn: str) -> None:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, category, item_name, aliases, variants FROM menu_items;"
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        self._items: dict[int, MenuItem] = {}
        for r in rows:
            variants = r["variants"] if isinstance(r["variants"], dict) else json.loads(r["variants"])
            base_price = Decimal(str(next(iter(variants.values()))))
            self._items[r["id"]] = MenuItem(
                id=r["id"],
                name=r["item_name"],
                price=base_price,
                aliases=tuple(r["aliases"] or ()),
                variants=variants,
            )

        self._index: dict[str, MenuItem] = {}
        for it in self._items.values():
            for key in (it.name, *it.aliases):
                self._index[normalize(key)] = it

    def get(self, item_id: int) -> MenuItem | None:
        return self._items.get(item_id)

    def find(self, text: str) -> MenuItem | None:
        return self._index.get(normalize(text))

    def all(self) -> list[MenuItem]:
        return list(self._items.values())


def build_menu() -> MenuProvider:
    """DATABASE_URL set + reachable -> SqlMenu (the one real menu).
    Anything fails -> InMemoryMenu fallback so the demo still boots."""
    dsn = os.getenv("DATABASE_URL", "")
    if dsn:
        try:
            menu = SqlMenu(dsn)
            print(f"[menu] loaded {len(menu.all())} items from Postgres")
            return menu
        except Exception as e:  # noqa: BLE001 - degrade, never crash the demo
            print(f"[menu] Postgres menu unavailable ({e}); falling back to in-memory seed")
    return InMemoryMenu()
