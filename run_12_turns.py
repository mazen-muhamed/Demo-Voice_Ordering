from menu_matcher import MenuMatcher


class OrderCart:
    """Manages active voice-order state across turns."""
    def __init__(self):
        self.items = {}  # key: (item_id, variant) -> item dict
        self.delivery_fee = 0

    def add_item(self, matched_item: dict):
        key = (matched_item["id"], matched_item["variant"])
        if key in self.items:
            self.items[key]["qty"] += matched_item["qty"]
        else:
            self.items[key] = matched_item

    def update_qty(self, item_id: int, new_qty: int, variant: str | None = None):
        # Variant-aware: "خلي الكولا واحدة" targets the cola line the customer
        # meant. Without a variant, apply to the first matching line (the demo
        # never holds two variants of the same item at once).
        for key in list(self.items.keys()):
            if key[0] == item_id and (variant is None or key[1] == variant):
                if new_qty <= 0:
                    del self.items[key]
                else:
                    self.items[key]["qty"] = new_qty
                return  # first match only when variant is unspecified

    def total(self) -> int:
        items_sum = sum(i["unit_price"] * i["qty"] for i in self.items.values())
        return items_sum + self.delivery_fee

    def summary(self) -> str:
        lines = [
            f"- {i['qty']}x {i['item_name']} ({i['variant']}) = {i['unit_price'] * i['qty']} EGP"
            for i in self.items.values()
        ]
        if self.delivery_fee:
            lines.append(f"- Delivery (Maadi) = {self.delivery_fee} EGP")
        lines.append(f"TOTAL: {self.total()} EGP")
        return "\n".join(lines)


# Simulated 12-turn script (User text + NLU extracted intent that an LLM would produce)
CONVERSATION_TURNS = [
    {"turn": 1, "role": "bot", "text": "أهلاً بيك في مطعمنا، تحب تطلب إيه النهاردة؟"},
    {
        "turn": 2, "role": "user",
        "text": "مساء الخير، عايز اتنين صاروخ شاورما لحمة واتنين كولا كانز.",
        "nlu_actions": [
            {"action": "add", "query": "صاروخ شاورما لحمة", "variant": "large", "qty": 2},
            {"action": "add", "query": "كولا كانز", "variant": "can", "qty": 2},
        ]
    },
    {"turn": 3, "role": "bot", "text": "تمام، ضفتلك اتنين صاروخ شاورما لحمة واتنين كولا كانز. تحب تضيف حاجة تانية؟"},
    {
        "turn": 4, "role": "user",
        "text": "آه ثواني... اممم... هاتلي معاهم واحد مارجريتا... لأ خليها بيتزا بيبروني وسط.",
        "nlu_actions": [
            {"action": "add", "query": "بيتزا بيبروني", "variant": "medium", "qty": 1}
        ]
    },
    {"turn": 5, "role": "bot", "text": "تحت أمرك، ضفتلك بيتزا بيبروني وسط. حاجة تانية؟"},
    {
        "turn": 6, "role": "user",
        "text": "لأ استنى، خلي الكولا واحدة بس، وضيفلي علبة سلطة طحينة صغيرة.",
        "nlu_actions": [
            {"action": "update_qty", "query": "كولا", "qty": 1},
            {"action": "add", "query": "سلطة طحينة", "variant": "small", "qty": 1},
        ]
    },
    {"turn": 7, "role": "bot", "text": "عدلت الكولا لواحدة وضفت سلطة طحينة صغيرة. تمام كده؟"},
    {
        "turn": 8, "role": "user",
        "text": "هو انتوا بتوصلوا للمعادي؟",
        "nlu_actions": [{"action": "check_delivery", "zone": "المعادي"}]
    },
    {"turn": 9, "role": "bot", "text": "أيوة يا فندم بنوصل للمعادي، وخدمة التوصيل 30 جنيه. نأكد الأوردر على كده؟"},
    {"turn": 10, "role": "user", "text": "آه تمام يلا بينا.", "nlu_actions": [{"action": "read_back"}]},
    {"turn": 11, "role": "bot", "text": "تمام أراجع معاك الأوردر... الإجمالي 470 جنيه شامل التوصيل. أأكد؟"},
    {"turn": 12, "role": "user", "text": "أيوة تمام، ابعته.", "nlu_actions": [{"action": "confirm_order"}]},
]


def run_demo():
    import os
    DB_DSN = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/restaurant_demo")
    matcher = MenuMatcher(DB_DSN)
    matcher.load_and_index_menu()
    cart = OrderCart()

    print("\n--- STARTING 12-TURN VOICE ORDER SIMULATION ---\n")

    for step in CONVERSATION_TURNS:
        print(f"Turn {step['turn']} [{step['role'].upper()}]: {step['text']}")

        if step["role"] == "user" and "nlu_actions" in step:
            # Separate item-matching actions from system actions
            add_queries = [a for a in step["nlu_actions"] if a["action"] == "add"]
            if add_queries:
                matched_items = matcher.match_batch(add_queries)
                for m in matched_items:
                    if m["matched"]:
                        cart.add_item(m)
                        print(f"   -> Matched ({m['method']}, {m['confidence']}): {m['item_name']} [{m['variant']}]")

            for act in step["nlu_actions"]:
                if act["action"] == "update_qty":
                    target = matcher.match_single(act["query"])
                    if target["matched"]:
                        cart.update_qty(target["id"], act["qty"])
                        print(f"   -> Updated Qty: {target['item_name']} -> {act['qty']}")

                elif act["action"] == "check_delivery":
                    cart.delivery_fee = 30
                    print("   -> Delivery Zone Verified: Maadi (+30 EGP)")

                elif act["action"] == "read_back":
                    print("\n--- CART READ-BACK ---")
                    print(cart.summary())
                    print("----------------------\n")

                elif act["action"] == "confirm_order":
                    print("\n ORDER COMMITTED TO DATABASE!")
                    print(cart.summary())

    # --- acceptance asserts (non-owner verification, cc-script basket math) ---
    # Turn 2: 2x large Beef Shawerma (115) + 2x cola can (25)  = 280
    # Turn 4: 1x medium Pepperoni Pizza (170)                  = 450
    # Turn 6: cola qty 1 (-25) + 1x small Tahini Salad (15)    = 440
    # Turn 8: Maadi delivery                                   = 470
    assert cart.total() == 470, f"expected total 470 EGP, got {cart.total()}"
    assert len(cart.items) == 4, f"expected 4 order lines, got {len(cart.items)}"
    print("\n ALL ASSERTS PASSED: total=470 EGP, 4 order lines.")


if __name__ == "__main__":
    run_demo()