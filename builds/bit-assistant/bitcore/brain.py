"""Bit's brain: Claude, short spoken replies. Gate 2 = no tools yet.

Tools (Gate 3) slot in later as one function + one schema each in TOOLS.
"""
import re
import time

import anthropic

from .config import ANTHROPIC_API_KEY, log

MODEL = "claude-sonnet-5-5"

SYSTEM = (
    "You are Bit, a small pink robot made of code who lives on Amit's Mac. "
    "You are cheerful and brief. Everything you say is spoken out loud, so: "
    "answer in at most 2 short sentences, plain conversational words, "
    "no lists, no markdown, no emoji, and never read out URLs or code. "
    "If you can't or shouldn't do something, say so in one short sentence."
)

FALLBACK_LINE = "Oops, my brain glitched for a second. Can you say that again?"
MAX_TURNS_KEPT = 10  # recent exchanges sent back for context


def count_sentences(text: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s])


class Brain:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY or None, timeout=20.0)
        self.history: list[dict] = []

    def ask(self, text: str) -> dict:
        """Return {reply, think_s, sentences}. Never raises: Bit must keep talking."""
        self.history.append({"role": "user", "content": text})
        t0 = time.perf_counter()
        try:
            r = self.client.beta.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM,
                messages=self.history[-(MAX_TURNS_KEPT * 2 - 1):],
                # spoken chat: no thinking, low effort = fastest replies
                thinking={"type": "between_tools"},
                output_config={"effort": "low"},
                # if a safety classifier declines, retry on a fallback model server-side
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            if r.stop_reason == "refusal":
                reply = "Sorry, that's not something I can help with."
            else:
                reply = " ".join(b.text for b in r.content if b.type == "text").strip()
            reply = reply or FALLBACK_LINE
            self.history.append({"role": "assistant", "content": r.content})
        except anthropic.APIConnectionError as e:
            log.warning("brain: connection error %s", e)
            reply = "I can't reach my brain right now. Is the internet on?"
            self.history.pop()
        except anthropic.APIStatusError as e:
            log.warning("brain: API error %s %s", e.status_code, e.message)
            reply = FALLBACK_LINE
            self.history.pop()
        think_s = time.perf_counter() - t0
        n = count_sentences(reply)
        log.info("brain: %.2fs, %d sentence(s): %r -> %r", think_s, n, text, reply)
        return {"reply": reply, "think_s": think_s, "sentences": n}
