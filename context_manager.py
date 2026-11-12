"""Week 2.2 digital-twin context selection prototype.

Uses conservative educational character-based token ESTIMATES, not a model tokenizer.
Never send sensitive source content to a remote service without authorization.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import logging
import math
import re
from typing import Callable


def estimate_tokens(text: str, chars_per_token: float = 4.0) -> int:
    """Estimate token usage; actual API counts depend on model/tokenizer."""
    if not isinstance(text, str):
        raise TypeError('text must be a string')
    if isinstance(chars_per_token, bool) or not isinstance(chars_per_token, (int, float)) or not math.isfinite(chars_per_token) or chars_per_token <= 0:
        raise ValueError('chars_per_token must be a positive finite number')
    return math.ceil(len(text) / chars_per_token)


def terms(text: str) -> set[str]:
    return set(re.findall(r"[\w]+", text.casefold()))


class ContextManager:
    """Build a bounded prompt from recent history and retrieved knowledge.

    Only prompt construction is implemented; no LLM call is made.
    Long-running history is stored in-memory. Keyword scoring is NOT semantic RAG.
    """

    def __init__(self, max_tokens: int = 600, system_reserve: int = 60,
                 response_reserve: int = 120, history_limit: int = 10,
                 chars_per_token: float = 4, debug: bool = False,
                 token_counter: Callable[[str], int] | None = None):
        for name, v in {'max_tokens': max_tokens, 'history_limit': history_limit,
                        'system_reserve': system_reserve, 'response_reserve': response_reserve}.items():
            if type(v) is not int or (v <= 0 if name in ('max_tokens', 'history_limit') else v < 0):
                raise ValueError(f'{name} must be an integer, positive for max_tokens/history_limit')
        if system_reserve + response_reserve >= max_tokens:
            raise ValueError('reserves must leave room for input')
        estimate_tokens('', chars_per_token)
        if token_counter is not None and not callable(token_counter):
            raise TypeError('token_counter must be callable')
        self.max_tokens = max_tokens
        self.budget = max_tokens - system_reserve - response_reserve
        self.history_limit = history_limit
        self.chars_per_token = chars_per_token
        self._external_counter = token_counter
        self.history: list[dict] = []
        self.knowledge: list[dict] = []
        self.reports: list[dict] = []
        self.logger = logging.getLogger(f'context_manager.{id(self)}')
        self.logger.setLevel(logging.DEBUG if debug else logging.WARNING)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            self.logger.addHandler(handler)
        self.logger.propagate = False

    def count(self, text: str) -> int:
        if not isinstance(text, str):
            raise TypeError('text must be a string')
        n = self._external_counter(text) if self._external_counter else estimate_tokens(text, self.chars_per_token)
        if type(n) is not int or n < 0:
            raise ValueError('token_counter must return a nonnegative integer')
        return n

    def ingest_chunks(self, chunks: list[dict]) -> int:
        """Integrate with Advanced 1's chunks.json list (text + metadata)."""
        if not isinstance(chunks, list):
            raise TypeError('chunks must be a list of dictionaries')
        validated = []
        for index, item in enumerate(chunks):
            if not isinstance(item, dict) or not isinstance(item.get('text'), str):
                raise ValueError(f'chunk {index} must be a dict with a text string')
            if item['text'].strip():
                validated.append({'text': item['text'].strip(),
                                  'source': str(item.get('source', 'unknown')),
                                  'chunk_id': str(item.get('chunk_id', item.get('id', index)))})
        self.knowledge.extend(validated)
        self.logger.debug('Added %d knowledge chunks', len(validated))
        return len(validated)

    def _truncate(self, text: str, budget: int) -> str:
        """Extractive trim, with explicit truncation marker where possible."""
        marker = ' [TRUNCATED]'
        if budget <= 0:
            return ''
        if self.count(text) <= budget:
            return text
        if self.count(marker) >= budget:
            return ''
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.count(text[:mid].rstrip() + marker) <= budget:
                lo = mid
            else:
                hi = mid - 1
        return text[:lo].rstrip() + marker if lo else ''

    def process(self, message: str, top_k: int = 3) -> dict:
        """Compose context prioritizing the newest user message, then knowledge, then history.

        Raises on oversized current messages rather than silently losing the question.
        Returns a report; also appends the original message to an in-memory history.
        """
        if not isinstance(message, str):
            raise TypeError('message must be a string')
        message = message.strip()
        if not message:
            raise ValueError('message cannot be blank')
        if type(top_k) is not int or top_k < 0:
            raise ValueError('top_k must be a nonnegative integer')
        reserved_for_message = self.count('USER: ' + message)
        if reserved_for_message > self.budget:
            raise ValueError('Current user message exceeds input budget; split or shorten it')

        remaining = self.budget - reserved_for_message
        blocks = []
        query_terms = terms(message)
        ranked = sorted(
            (k for k in self.knowledge if query_terms & terms(k['text'])),
            key=lambda k: (-len(query_terms & terms(k['text'])), k['chunk_id'])
        )[:top_k]
        for k in ranked:
            block = f"KNOWLEDGE ({k['source']} / {k['chunk_id']}): {k['text']}"
            if self.count(block) <= remaining:
                blocks.append({'role': 'knowledge', 'text': block, 'source': k['source']})
                remaining -= self.count(block)
            else:
                trimmed = self._truncate(block, remaining)
                if trimmed:
                    blocks.append({'role': 'knowledge', 'text': trimmed, 'source': k['source']})
                    remaining -= self.count(trimmed)
                break

        # Sliding window: recency priority, preserving chronological order at output.
        recent = self.history[-self.history_limit:]
        selected = []
        for entry in reversed(recent):
            block = f"{entry['role'].upper()}: {entry['content']}"
            if self.count(block) <= remaining:
                selected.append({'role': 'history', 'text': block})
                remaining -= self.count(block)
            else:
                trimmed = self._truncate(block, remaining)
                if trimmed:
                    selected.append({'role': 'history', 'text': trimmed})
                    remaining -= self.count(trimmed)
                break
        selected.reverse()
        components = blocks + selected + [{'role': 'user', 'text': 'USER: ' + message}]
        prompt = '\n\n'.join(c['text'] for c in components)
        # Joining/formatting consumes tokens too; drop least-priority items if needed.
        while self.count(prompt) > self.budget and len(components) > 1:
            components.pop(-2)
            prompt = '\n\n'.join(c['text'] for c in components)
        used = self.count(prompt)
        if used > self.budget:
            raise ValueError('Message plus prompt formatting exceeds input budget')
        naive = '\n\n'.join(
            [f"KNOWLEDGE: {k['text']}" for k in ranked] +
            [f"{h['role'].upper()}: {h['content']}" for h in recent] +
            ['USER: ' + message]
        )
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'max_tokens': self.max_tokens,
            'input_budget': self.budget,
            'before_tokens': self.count(naive),
            'after_tokens': used,
            'remaining_input_tokens': self.budget - used,
            'history_included': sum(c['role'] == 'history' for c in components),
            'knowledge_included': sum(c['role'] == 'knowledge' for c in components),
            'compressed': used < self.count(naive),
            'prompt': prompt,
        }
        self.history.append({'role': 'user', 'content': message})
        self.reports.append(report)
        self.logger.debug('Prompt tokens: %d -> %d (budget %d)', report['before_tokens'], used, self.budget)
        return report

    def add_assistant_message(self, text: str):
        if not isinstance(text, str) or not text.strip():
            raise ValueError('assistant message must be nonblank text')
        self.history.append({'role': 'assistant', 'content': text.strip()})

    def visualize(self):
        """Plot prior to/from optimization; Matplotlib required."""
        if not self.reports:
            raise ValueError('No processing reports to visualize')
        import matplotlib.pyplot as plt
        xs = list(range(1, len(self.reports) + 1))
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(xs, [x['before_tokens'] for x in self.reports], marker='o', label='Before selection')
        ax.plot(xs, [x['after_tokens'] for x in self.reports], marker='o', label='After selection')
        ax.axhline(self.budget, linestyle='--', label='Input budget')
        ax.set(xlabel='Conversation turn', ylabel='Estimated tokens', title='Digital Twin Context Usage')
        ax.set_xticks(xs)
        ax.legend()
        fig.tight_layout()
        return fig
