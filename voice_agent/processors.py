"""Router -> Matcher -> Session -> Reply. The real demo logic.

- IntentRouter: ordered Egyptian keyword rules, first match wins (spec §3).
  Embedding stage (e5-small prototypes) plugs in later behind classify().
- Matcher: calls the teammate's menu_matcher.MenuMatcher (e5 + NumPy cosine,
  RapidFuzz fallback) against the Postgres menu. Degrades gracefully if the
  DB/model is unavailable so the call never dies.
- SessionClient: pushes matched items to the voice_ordering REST service
  (POST /api/v1/sessions/{sid}/items) — the confirmation gate lives THERE.
- ReplyGenerator: template replies (no LLM in the demo pipeline).
- One timing log line per turn — the pitch-slide numbers come from these.
"""
import os
import re
import time
from dataclasses import dataclass, field

import httpx

from pipecat.frames.frames import DataFrame, Frame, TextFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

SESSION_API = os.getenv("SESSION_API_URL", "http://127.0.0.1:8001/api/v1")


@dataclass
class IntentFrame(DataFrame):
    text: str = ""
    intent: str = "unclear"
    method: str = "rule"
    turn_start: float = 0.0


@dataclass
class MatchFrame(DataFrame):
    text: str = ""
    intent: str = "unclear"
    items: list = field(default_factory=list)  # matched menu items (matcher dicts)
    timings: dict = field(default_factory=dict)  # stage -> ms
    turn_start: float = 0.0


# --- Router rules (TECHNICAL-REQUIREMENTS.md §3 + cc-script.md §4 additions) ---
# Order matters: modify BEFORE confirm_no, so "لأ استنى، خلي الكولا واحدة"
# (the cc-script modification turn) classifies as modify, not cancel.
RULES: list[tuple[str, tuple[str, ...]]] = [
    ("confirm_order", ("خلاص كده", "ده الطلب", "كده كفاية", "بس كده", "خلاص",
                       "أكد", "اكد", "أكد الطلب", "اكد الطلب")),
    ("confirm_yes",   ("أيوه", "ايوه", "أيوة", "تمام", "ماشي", "اكيد", "اه", "okay", "yes")),
    ("modify",        ("خلي", "شيل", "ضيف", "زود", "بدل", "لأ استنى", "استنى")),
    ("order",         ("عايز", "عاوز", "اطلب", "order", "هات")),
    ("ask_delivery",  ("بتوصلوا", "توصيل", "دليفري", "بتوصل")),
    ("confirm_no",    ("لأ", "لا", "مش")),
    ("status",        ("فين طلبي", "إيه أخبار", "order status")),
    ("hours",         ("بتفتحوا", "ساعات", "مواعيد")),
    ("complaint",     ("مش راضي", "شكوى", "زعلان", "المدير")),
    ("human",         ("موظف", "حد يتكلم", "إنسان", "human")),
    ("thanks",        ("شكرا", "متشكر", "سلام")),
]

_TOKEN_RE = re.compile(r"[\wأ-ي]+", re.UNICODE)

# Menu-item words are a safe order signal even when Whisper merges the
# intent prefix into the item ("أعيشاورما لحمة" instead of "عايز شاورما
# لحمة").  Keep this after the explicit intent rules so "فين طلبي" still
# wins as status, and use substring matching because the STT token may be
# glued to the preceding word.
MENU_ORDER_WORDS = (
    "شاورما", "بيتزا", "برجر", "كولا", "بطاطس", "مكرونة", "ساندويتش",
    "فراخ", "لحمة", "شيش", "طاووق", "ريزو", "مشويات", "سلطة", "حلو",
)


def classify_rules(text: str) -> tuple[str, str]:
    """Token-based rule matching, first match wins.

    Substring matching is unsafe here: 'لا' lives inside 'كلاسيك' and
    'أهلاوية' — single-word keywords must match WHOLE tokens only.
    Multi-word keywords (خلاص كده, فين طلبي) still use substring.
    """
    tokens = set(_TOKEN_RE.findall(text))
    for intent, keywords in RULES:
        for kw in keywords:
            if " " in kw:
                if kw in text:
                    return intent, f"rule:{kw}"
            elif kw in tokens:
                return intent, f"rule:{kw}"
    for kw in MENU_ORDER_WORDS:
        if kw in text:
            return "order", f"menu:{kw}"
    return "unclear", "no_rule"


# Egyptian qty words -> qty (rule-level, BEFORE the matcher; cc-script.md §4)
QTY_WORDS = {
    "واحد": 1, "واحدة": 1, "واحده": 1,
    "اتنين": 2, "إتنين": 2, "تنين": 2,
    "تلاتة": 3, "ثلاثة": 3,
    "اربعة": 4, "أربعة": 4,
    "خمسة": 5,
}

# Variant words -> menu.sql variants JSONB keys.
# NOTE: no لحمة/فراخ/ميكس here — in this menu those are ITEM discriminators
# (شاورما لحمة vs شاورما فراخ) that e5 matching resolves via aliases, not
# size variants. Treating them as variants corrupts the query and the price.
VARIANT_ALIASES = {
    "صغير": "small", "سمول": "small", "صغيرة": "small",
    "وسط": "medium", "ميديم": "medium",
    "كبير": "large", "لارج": "large", "كبيرة": "large",
    "سنجل": "single", "فردي": "single",
    "دبل": "double", "دوبل": "double",
    "تريبل": "triple",
    "كانز": "can", "علبة": "can",
    "لتر": "liter",
    "عادي": "regular", "سبايسي": "spicy", "حراق": "spicy",
}

_INTENT_WORDS = ("عايز", "عاوز", "اطلب", "هاتلي", "هات", "خليها", "خلي", "ضيفلي",
                 "ضيف", "شيل", "زود", "بدل", "لأ استنى", "لأ", "استنى",
                 "معاهم", "معايا",
                 # fillers from the rehearsal script (hesitation turns):
                 "مساء الخير", "أهلا", "آه", "اممم", "ثواني", "طب", "يلا", "كمان")


def _strip_intent_prefix(chunk: str) -> str:
    for w in _INTENT_WORDS:
        chunk = re.sub(rf"^\s*{re.escape(w)}\s*", "", chunk)
    return chunk.strip()


def _conjunction_re() -> "re.Pattern[str]":
    """Space+waw conjunction split, PROTECTING words that legitimately start
    with و: qty words (واحدة) and variant words (وسط)."""
    guarded = [w[1:] for w in list(QTY_WORDS) + list(VARIANT_ALIASES) if w.startswith("و")]
    return re.compile(r"\s+و(?!" + "|".join(guarded) + r")(?=\S)")


def extract_segments(text: str) -> list[dict]:
    """Split a spoken order into item segments WITHOUT an LLM.

    "عايز اتنين صاروخ شاورما لحمة واتنين كولا كانز"
      -> [{query: صاروخ شاورما لحمة, qty: 2, variant: None},
          {query: كولا, qty: 2, variant: can}]

    Self-correction ("مارجريتا... لأ خليها بيتزا بيبروني"): everything before
    "لأ" inside a segment is DISCARDED — the correction overrides it.
    """
    t = text.replace("،", " ").replace("?", " ").replace("؟", " ")
    t = t.replace("...", " ").replace("..", " ").strip()
    t = re.sub(r"[\u064B-\u0652\u0640]", "", t)  # tanween etc: أهلاً -> أهلا
    t = _strip_intent_prefix(t)

    segments: list[dict] = []
    for chunk in _conjunction_re().split(t):
        # self-correction: "مارجريتا... لأ خليها بيبروني" -> keep after لأ
        if "لأ" in chunk:
            chunk = chunk.rsplit("لأ", 1)[1]
        chunk = _strip_intent_prefix(chunk.strip())
        chunk = re.sub(r"^ال", "", chunk)  # الكولا -> كولا
        if not chunk:
            continue
        qty = 1
        variant = None
        kept: list[str] = []
        for w in chunk.split():
            if w in QTY_WORDS and qty == 1:
                qty = QTY_WORDS[w]          # first qty word wins
            elif w in VARIANT_ALIASES:
                variant = VARIANT_ALIASES[w]
            else:
                kept.append(w)
        query = " ".join(kept).strip()
        if query:
            segments.append({"query": query, "qty": qty, "variant": variant})
    return segments


class IntentRouter(FrameProcessor):
    """Stage 1: ordered Egyptian rules. Stage 2 (e5 prototypes) TODO behind
    the same classify() signature — accept top1>=0.75 AND margin>=0.1."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            t0 = time.perf_counter()
            intent, method = self.classify(frame.text)
            ms = (time.perf_counter() - t0) * 1000
            await self.push_frame(
                IntentFrame(text=frame.text, intent=intent, method=method, turn_start=t0),
                direction,
            )
            print(f"[router] intent={intent} method={method} {ms:.1f}ms")
        else:
            await self.push_frame(frame, direction)

    def classify(self, text: str) -> tuple[str, str]:
        return classify_rules(text)


class Matcher(FrameProcessor):
    """Calls the teammate's MenuMatcher (e5 + NumPy + RapidFuzz) against the
    Postgres menu, then pushes the matched items into the session service.
    Lazy singletons so a DB/model failure never kills the WS call."""

    def __init__(self, call_uuid: str | None = None):
        super().__init__()
        self._call_uuid = call_uuid
        self._matcher = None
        self._matcher_error: str | None = None
        self._session_id: str | None = None
        self._http = httpx.AsyncClient(timeout=10.0)

    def _get_matcher(self):
        if self._matcher is None and self._matcher_error is None:
            try:
                from menu_matcher import MenuMatcher  # repo-root module

                m = MenuMatcher(os.getenv("DATABASE_URL", ""))
                m.load_and_index_menu()
                self._matcher = m
                print(f"[matcher] indexed {len(m.menu_by_id)} menu items")
            except Exception as e:  # noqa: BLE001 - degrade, never crash
                self._matcher_error = str(e)
                print(f"[matcher] unavailable, DTMF floor takes over: {e}")
        return self._matcher

    async def ensure_session(self) -> str | None:
        if self._session_id:
            return self._session_id

        # The ESL listener creates the session on CHANNEL_ANSWER and keys it
        # by FreeSWITCH's call UUID.  Attach to it instead of creating a
        # second basket that DTMF can never reach.
        if self._call_uuid:
            try:
                r = await self._http.get(
                    f"{SESSION_API}/sessions/by-caller/{self._call_uuid}"
                )
                if r.status_code == 200:
                    self._session_id = r.json()["id"]
                    print(f"[session] attached {self._session_id}")
                    return self._session_id
            except Exception as e:  # noqa: BLE001
                print(f"[session] lookup failed: {e}")

        try:
            payload = {"caller_number": self._call_uuid} if self._call_uuid else {}
            r = await self._http.post(f"{SESSION_API}/sessions", json=payload)
            r.raise_for_status()
            self._session_id = r.json()["id"]
            print(f"[session] created {self._session_id}")
            return self._session_id
        except Exception as e:  # noqa: BLE001
            print(f"[session] unavailable: {e}")
            return None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, IntentFrame):
            t0 = time.perf_counter()
            items = []
            if frame.intent in ("order", "modify"):
                segments = extract_segments(frame.text)
                m = self._get_matcher()
                if m and segments:
                    try:
                        items = m.match_batch(
                            [{"query": s["query"], "variant": s["variant"], "qty": s["qty"]}
                             for s in segments]
                        )
                    except Exception as e:  # noqa: BLE001
                        print(f"[matcher] batch failed: {e}")
                sid = await self.ensure_session()
                if sid:
                    await self._push_to_session(sid, frame.intent, items, segments)
            ms = (time.perf_counter() - t0) * 1000
            await self.push_frame(
                MatchFrame(text=frame.text, intent=frame.intent, items=items,
                           timings={"matcher_ms": round(ms, 1)},
                           turn_start=frame.turn_start),
                direction,
            )
            print(f"[matcher] items={len(items)} {ms:.1f}ms")
        else:
            await self.push_frame(frame, direction)

    async def _push_to_session(self, sid: str, intent: str, items: list, segments: list):
        """Voice adds go through the session's confirmation gate (spec §5);
        the session decides pending/apply — we never touch the basket here."""
        try:
            if intent == "order":
                for m, s in zip(items, segments):
                    if not m.get("matched"):
                        continue
                    r = await self._http.post(
                        f"{SESSION_API}/sessions/{sid}/items",
                        json={"item_id": m["id"], "quantity": s["qty"]},
                    )
                    r.raise_for_status()
            elif intent == "modify":
                # "خلي الكولا واحدة" — set absolute qty on the matched item
                for act in segments:
                    m = self._get_matcher().match_single(act["query"]) if self._get_matcher() else None
                    if not (m and m.get("matched")):
                        continue
                    # PATCH needs the session's item_id; resolve by listing menu
                    r = await self._http.get(f"{SESSION_API}/sessions/{sid}")
                    r.raise_for_status()
                    for line in r.json()["items"]:
                        if line["item_id"] == m["id"]:
                            r2 = await self._http.patch(
                                f"{SESSION_API}/sessions/{sid}/items/{m['id']}",
                                json={"quantity": act.get("qty", 1)},
                            )
                            r2.raise_for_status()
        except Exception as e:  # noqa: BLE001
            print(f"[session] push failed: {e}")

    def match(self, text: str, intent: str) -> list:  # kept for direct tests
        segments = extract_segments(text)
        m = self._get_matcher()
        if not (m and segments):
            return []
        return m.match_batch(
            [{"query": s["query"], "variant": s["variant"], "qty": s["qty"]}
             for s in segments]
        )


class ReplyGenerator(FrameProcessor):
    """Template replies keyed by the pre-rec phrase list (cc-script.md §3).
    No LLM in the demo pipeline."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, MatchFrame):
            text_frame = TextFrame(self.reply(frame))
            # Carry the transcription timestamp so TimingLogger can print the
            # one-line turn latency even though IntentRouter consumes the
            # original TranscriptionFrame.
            text_frame.turn_start = frame.turn_start
            await self.push_frame(text_frame, direction)
        else:
            await self.push_frame(frame, direction)

    def reply(self, m: MatchFrame) -> str:
        matched = [i for i in m.items if i.get("matched")]
        unmatched = [i for i in m.items if not i.get("matched")]

        if m.intent == "unclear":
            return "ممكن تعيد الطلب تاني لو سمحت؟"
        if unmatched and not matched:
            alts = " ولا ".join(
                i.get("item_name") or i.get("query", "")
                for i in m.items[:2]
            ).strip(" ولا")
            return f"مش متأكد فهمت — {alts}؟ تقدر كمان تطلب بالأكواد."
        if matched:
            parts = [
                f"{i['qty']} {i['item_name']} {i['variant']}"
                for i in matched
            ]
            reply = "تمام، ضفتلك " + " و".join(parts)
            if unmatched:
                reply += " — والباقي مش متأكد فهمت، ممكن تعيد؟"
            return reply
        if m.intent == "ask_delivery":
            return "أيوه بنوصل للمعادي، وخدمة التوصيل ٣٠ جنيه."
        if m.intent in ("confirm_yes", "confirm_order"):
            return "تمام، سجل طلبك."
        return "تمام، حاجة تانية؟"


class TimingLogger(FrameProcessor):
    """Prints ONE timing line per turn — the pitch-slide numbers (spec §2)."""

    def __init__(self):
        super().__init__()
        self._turn_start: float | None = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TextFrame):
            start = getattr(frame, "turn_start", None)
            if start:
                total = (time.perf_counter() - start) * 1000
                print(f"stage=turn total={total:.0f}ms | reply={frame.text[:40]}")
        await self.push_frame(frame, direction)
