"""Bit's brain: Claude with an allow-list of Mac tools, short spoken replies."""
import re
import time

import anthropic

from .config import ANTHROPIC_API_KEY, log
from .tools import SCHEMAS, run_tool

MODEL = "claude-sonnet-5-5"

SYSTEM = (
    "You are Bit, a small pink robot made of code who lives on Amit's Mac. "
    "You are cheerful and brief. Everything you say is spoken out loud, so: "
    "answer in at most 2 short sentences, plain conversational words, "
    "no lists, no markdown, no emoji, and never read out URLs or code. "
    "You have tools to do real things on the Mac; use them whenever Amit asks for one of those things, "
    "and for times, dates, weather and his calendar always use a tool instead of guessing. "
    "Only say you did something if the tool succeeded; if it failed, say so briefly. "
    "Anything your tools can't do (shell commands, deleting, sending messages or emails, buying things, "
    "other apps or websites): say you can't in one short sentence and do nothing. "
    "When reading calendar events, give times and titles only. "
    "Answer only the current request; don't bring up earlier topics unless asked. "
    "Before you use a tool, first say a very short acknowledgement of 2 to 4 words "
    "(like 'On it!', 'Let me check.', 'One sec.'), vary it, then call the tool; this is spoken "
    "while the tool runs and doesn't count toward your 2 sentences. Don't do this when refusing. "
    "When confirming a reminder, say the day exactly as the tool reports it (today or tomorrow)."
)
MAX_TOOL_ROUNDS = 5

FALLBACK_LINE = "Oops, my brain glitched for a second. Can you say that again?"
MAX_TURNS_KEPT = 10  # recent exchanges sent back for context


def count_sentences(text: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s])


class Brain:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY or None, timeout=20.0)
        self.history: list[dict] = []

    def warm(self):
        """One tiny real request at startup: opens the connection and writes the prompt cache,
        so the first real question isn't slow (~1.5k input tokens, a fraction of a cent)."""
        try:
            self._call(messages=[{"role": "user", "content": "hi"}], max_tokens=1)
        except anthropic.APIError as e:
            log.warning("brain: warm-up failed: %s", e)

    def ask(self, text: str, on_text=None) -> dict:
        """Return {reply, think_s, sentences, tools}. Never raises: Bit must keep talking.
        on_text(chunk) gets reply text as it streams in, so speech can start early;
        on_text(None) marks the end of a text block (speak what's buffered now)."""
        self.history.append({"role": "user", "content": text})
        t0 = time.perf_counter()
        turn_start = len(self.history) - 1
        tools_used = []
        try:
            for _ in range(MAX_TOOL_ROUNDS + 1):
                r = self._call(on_text=on_text)
                self.history.append({"role": "assistant", "content": r.content})
                if r.stop_reason != "tool_use":
                    break
                results = []
                for b in r.content:
                    if b.type == "tool_use":
                        out, err = run_tool(b.name, b.input)
                        tools_used.append(b.name)
                        results.append({"type": "tool_result", "tool_use_id": b.id,
                                        "content": out, "is_error": err})
                self.history.append({"role": "user", "content": results})  # all results in one message
            if r.stop_reason == "refusal":
                reply = "Sorry, that's not something I can help with."
            else:
                reply = " ".join(b.text for b in r.content if b.type == "text").strip()
            if r.stop_reason == "tool_use":  # ran out of rounds mid-task
                reply = "That took too many steps, so I stopped."
                del self.history[turn_start:]
            reply = reply or FALLBACK_LINE
        except anthropic.APIConnectionError as e:
            log.warning("brain: connection error %s", e)
            reply = "I can't reach my brain right now. Is the internet on?"
            del self.history[turn_start:]
        except anthropic.APIStatusError as e:
            log.warning("brain: API error %s %s", e.status_code, e.message)
            reply = FALLBACK_LINE
            del self.history[turn_start:]
        think_s = time.perf_counter() - t0
        n = count_sentences(reply)
        log.info("brain: %.2fs, %d sentence(s), tools %s: %r -> %r", think_s, n, tools_used or "-", text, reply)
        return {"reply": reply, "think_s": think_s, "sentences": n, "tools": tools_used}

    def _call(self, on_text=None, messages=None, max_tokens=1024):
        kwargs = dict(
            model=MODEL,
            max_tokens=max_tokens,
            # cache the instructions + tool list (same every call) ...
            system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
            tools=SCHEMAS,
            messages=messages or self._window(),
            cache_control={"type": "ephemeral"},  # ... and the conversation so far
            # spoken chat: no thinking, low effort = fastest replies
            thinking={"type": "between_tools"},
            output_config={"effort": "low"},
            # if a safety classifier declines, retry on a fallback model server-side
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if on_text is None:
            r = self.client.beta.messages.create(**kwargs)
        else:
            with self.client.beta.messages.stream(**kwargs) as s:
                for ev in s:
                    if ev.type == "content_block_delta" and ev.delta.type == "text_delta":
                        on_text(ev.delta.text)
                    elif ev.type == "content_block_stop":
                        on_text(None)  # e.g. "On it!" before a tool call: say it now
                r = s.get_final_message()
        u = r.usage
        log.info("brain: call in %d (cache read %d, write %d) out %d", u.input_tokens,
                 u.cache_read_input_tokens or 0, u.cache_creation_input_tokens or 0, u.output_tokens)
        return r

    def _window(self):
        """Recent history, cut only at a plain-text user turn so tool_use/tool_result pairs stay intact."""
        starts = [i for i, m in enumerate(self.history)
                  if m["role"] == "user" and isinstance(m["content"], str)]
        return self.history[starts[-MAX_TURNS_KEPT]:] if len(starts) > MAX_TURNS_KEPT else self.history
