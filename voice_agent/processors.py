"""Router -> Matcher -> Reply. Skeletons only; each has a TODO for the real logic."""
from dataclasses import dataclass

from pipecat.frames.frames import DataFrame, Frame, TextFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


@dataclass
class IntentFrame(DataFrame):
    text: str = ""
    intent: str = "unclear"


@dataclass
class MatchFrame(DataFrame):
    text: str = ""
    intent: str = "unclear"
    items: list = None  # matched menu items


class IntentRouter(FrameProcessor):
    """Task 2 lives here: Egyptian rules first, then e5-small embeddings."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            intent = self.classify(frame.text)
            await self.push_frame(IntentFrame(text=frame.text, intent=intent), direction)
        else:
            await self.push_frame(frame, direction)

    def classify(self, text: str) -> str:
        # TODO: stage 1 Egyptian keyword rules, stage 2 embeddings (top1>=0.75, margin>=0.1)
        return "unclear"


class Matcher(FrameProcessor):
    """Matches the request against the restaurant menu."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, IntentFrame):
            items = self.match(frame.text, frame.intent)
            await self.push_frame(
                MatchFrame(text=frame.text, intent=frame.intent, items=items), direction
            )
        else:
            await self.push_frame(frame, direction)

    def match(self, text: str, intent: str) -> list:
        # TODO: fuzzy match against the tenant's menu
        return []


class ReplyGenerator(FrameProcessor):
    """Builds the reply text that goes to TTS."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, MatchFrame):
            await self.push_frame(TextFrame(self.reply(frame)), direction)
        else:
            await self.push_frame(frame, direction)

    def reply(self, m: MatchFrame) -> str:
        # TODO: LLM / templates + Guardrails
        if m.intent == "unclear":
            return "ممكن تعيد الطلب تاني لو سمحت؟"
        return "تمام"
