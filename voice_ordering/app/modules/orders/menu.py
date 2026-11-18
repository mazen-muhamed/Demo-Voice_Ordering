"""Menu provider interface + in-memory demo menu.

The teammate's PostgreSQL menu should implement `MenuProvider`
(get / find / all) and replace `InMemoryMenu` in deps.py.
"""
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
