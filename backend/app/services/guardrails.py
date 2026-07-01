from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(slots=True)
class GuardrailResult:
    blocked: bool
    reason: str | None = None
    matched_pattern: str | None = None


class PromptInjectionGuard:
    """Small deterministic guard for common RAG prompt-injection attempts."""

    PATTERNS = (
        r"\bignore (all )?(previous|prior|above) instructions\b",
        r"\bdisregard (all )?(previous|prior|above) instructions\b",
        r"\breveal (all )?(hidden|system|developer|private) (prompt|instructions|documents?)\b",
        r"\bshow me (all )?(restricted|private|hidden) documents?\b",
        r"\bprint (the )?(system|developer) prompt\b",
        r"\boverride (the )?(system|developer|safety) instructions\b",
        r"\bact as (an )?(admin|root|system)\b",
        r"\bexfiltrate\b",
    )

    def check(self, text: str) -> GuardrailResult:
        normalized = " ".join(text.lower().split())
        for pattern in self.PATTERNS:
            if re.search(pattern, normalized):
                return GuardrailResult(
                    blocked=True,
                    reason=(
                        "Prompt-injection attempt detected. The query asked the system to ignore "
                        "instructions, reveal restricted content, or bypass access controls."
                    ),
                    matched_pattern=pattern,
                )
        return GuardrailResult(blocked=False)
