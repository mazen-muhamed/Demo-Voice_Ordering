import re
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from rapidfuzz import process, fuzz


def normalize_arabic(text: str) -> str:
    """Normalize Egyptian Arabic & STT quirks before matching."""
    text = text.strip().lower()
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text)


class MenuMatcher:
    def __init__(self, db_dsn: str, model_name: str = "intfloat/multilingual-e5-small"):
        self.db_dsn = db_dsn
        self.model = SentenceTransformer(model_name)

        self.menu_by_id = {}
        self.phrase_bank = []      # Normalized aliases
        self.phrase_to_id = []     # Maps each alias back to menu_items.id
        self.phrase_embeddings = None

    def load_and_index_menu(self):
        """Load your exact menu_items table and pre-compute e5 vectors."""
        conn = psycopg2.connect(self.db_dsn)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, category, item_name, aliases, variants FROM menu_items;")
            rows = cur.fetchall()
        conn.close()

        self.menu_by_id.clear()
        self.phrase_bank.clear()
        self.phrase_to_id.clear()

        for row in rows:
            item_id = row["id"]
            self.menu_by_id[item_id] = dict(row)

            # Index English item_name + all Arabic aliases
            all_phrases = set([row["item_name"]] + (row["aliases"] or []))
            for phrase in all_phrases:
                norm_phrase = normalize_arabic(phrase)
                self.phrase_bank.append(norm_phrase)
                self.phrase_to_id.append(item_id)

        passages = [f"passage: {p}" for p in self.phrase_bank]
        self.phrase_embeddings = self.model.encode(
            passages,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        print(f"Indexed {len(self.menu_by_id)} items ({len(self.phrase_bank)} aliases).")

    def match_single(self, raw_query: str, variant_key: str = None, vec_threshold: float = 0.84, item_margin: float = 0.02, fuzzy_threshold: int = 75) -> dict:
        """
        Match a spoken item phrase (e.g., 'صاروخ شاورما لحمة') and resolve variant price.

        Acceptance is ITEM-level: e5-small scores every Arabic phrase high
        (garbage like 'لبس أهلاوية' hits 0.88), so a bare score threshold
        silently orders the wrong dish. The best item must beat the best
        OTHER item by `item_margin` — aliases of the same item don't count
        as competition. Measured: real matches 0.020-0.066 gap, garbage
        0.000-0.008.
        """
        norm_query = normalize_arabic(raw_query)

        # 1. E5 Vector + NumPy Brute-Force Cosine Similarity
        query_vec = self.model.encode(
            [f"query: {norm_query}"],
            normalize_embeddings=True,
            convert_to_numpy=True
        )[0]

        scores = np.dot(self.phrase_embeddings, query_vec)
        best_idx = int(np.argmax(scores))
        best_vec_score = float(scores[best_idx])

        # Item-level ranking: best score per item, best vs runner-up ITEM
        item_best: dict[int, float] = {}
        for phrase_idx, score in enumerate(scores):
            iid = self.phrase_to_id[phrase_idx]
            if score > item_best.get(iid, -1.0):
                item_best[iid] = float(score)
        ranked = sorted(item_best.items(), key=lambda kv: kv[1], reverse=True)
        best_item_id, best_item_score = ranked[0]
        runner_item_score = ranked[1][1] if len(ranked) > 1 else 0.0

        matched_id = None
        method = "none"
        confidence = round(best_vec_score, 3)

        if best_item_score >= vec_threshold and (best_item_score - runner_item_score) >= item_margin:
            matched_id = best_item_id
            method = "e5_vector"
        else:
            # 2. RapidFuzz Fallback
            fuzzy_match = process.extractOne(norm_query, self.phrase_bank, scorer=fuzz.WRatio)
            if fuzzy_match and fuzzy_match[1] >= fuzzy_threshold:
                _, fuzzy_score, fuzzy_idx = fuzzy_match
                matched_id = self.phrase_to_id[fuzzy_idx]
                method = "rapidfuzz_fallback"
                confidence = round(fuzzy_score / 100.0, 3)

        if not matched_id:
            return {"query": raw_query, "matched": False, "method": "none", "confidence": confidence}

        item = self.menu_by_id[matched_id]
        variants = item["variants"]  # e.g. {"small": 65, "medium": 90, "large": 115}

        # Pick requested variant, or default to the first variant in the JSONB object
        selected_variant = variant_key if (variant_key and variant_key in variants) else next(iter(variants))
        unit_price = variants[selected_variant]

        return {
            "query": raw_query,
            "matched": True,
            "method": method,
            "confidence": confidence,
            "id": item["id"],
            "item_name": item["item_name"],
            "variant": selected_variant,
            "unit_price": unit_price,
            "all_variants": variants
        }

    def match_batch(self, items: list[dict]) -> list[dict]:
        """
        Accepts 1 to 5 extracted items from a turn:
        [{"query": "شاورما لحمة", "variant": "large", "qty": 2}, ...]
        """
        if not (1 <= len(items) <= 5):
            raise ValueError("Batch must contain between 1 and 5 items.")
        
        results = []
        for entry in items:
            res = self.match_single(entry["query"], entry.get("variant"))
            res["qty"] = entry.get("qty", 1)
            if res["matched"]:
                res["line_total"] = res["unit_price"] * res["qty"]
            results.append(res)
        return results