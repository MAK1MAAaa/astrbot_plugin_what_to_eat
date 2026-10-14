"""按会话记录响应次数和复读冷却，两项保护相互独立。"""

from __future__ import annotations

import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass

SessionKey = tuple[str, str, str]


@dataclass
class _SessionState:
    responses: deque[float]
    last_echo: float | None = None


class RateLimiter:
    """同步检查与记录；超过次数时强制推荐，仍然响应消息。"""

    def __init__(
        self,
        max_responses: int = 3,
        window_seconds: int = 60,
        echo_cooldown_enabled: bool = True,
        echo_cooldown_seconds: int = 15,
        *,
        rate_limit_enabled: bool = True,
        max_entries: int = 2048,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.max_responses = self._integer(max_responses, 3, 1)
        self.window_seconds = self._integer(window_seconds, 60, 1)
        self.rate_limit_enabled = (
            rate_limit_enabled if isinstance(rate_limit_enabled, bool) else True
        )
        self.echo_cooldown_enabled = (
            echo_cooldown_enabled if isinstance(echo_cooldown_enabled, bool) else True
        )
        self.echo_cooldown_seconds = min(
            3600, self._integer(echo_cooldown_seconds, 15, 0)
        )
        self.max_entries = self._integer(max_entries, 2048, 1)
        self._clock = clock if clock is not None else time.monotonic
        self._sessions: OrderedDict[SessionKey | str, _SessionState] = OrderedDict()

    @staticmethod
    def _integer(value: object, default: int, minimum: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            return default
        return max(minimum, value)

    def _cleanup(self, now: float) -> None:
        for key, state in list(self._sessions.items()):
            cutoff = now - self.window_seconds
            while state.responses and state.responses[0] <= cutoff:
                state.responses.popleft()
            if (
                state.last_echo is not None
                and now - state.last_echo >= self.echo_cooldown_seconds
            ):
                state.last_echo = None
            if not state.responses and state.last_echo is None:
                del self._sessions[key]

    def _state(self, key: SessionKey | str) -> _SessionState:
        state = self._sessions.get(key)
        if state is None:
            # 判断是否达到阈值只需保留最近 max_responses 个时间戳。
            state = _SessionState(deque(maxlen=self.max_responses))
            self._sessions[key] = state
        self._sessions.move_to_end(key)
        while len(self._sessions) > self.max_entries:
            self._sessions.popitem(last=False)
        return state

    def can_respond(self, key: SessionKey | str) -> tuple[bool, bool]:
        self._cleanup(self._clock())
        state = self._sessions.get(key)
        force_recommend = (
            bool(key)
            and self.rate_limit_enabled
            and state is not None
            and len(state.responses) >= self.max_responses
        )
        return True, force_recommend

    def record_response(self, key: SessionKey | str) -> None:
        now = self._clock()
        self._cleanup(now)
        if key and self.rate_limit_enabled:
            self._state(key).responses.append(now)

    def check_and_record(self, key: SessionKey | str) -> tuple[bool, bool]:
        # AstrBot 的事件协程在此处没有 await，不会在检查与占位之间切换。
        can_respond, force_recommend = self.can_respond(key)
        if can_respond:
            self.record_response(key)
        return can_respond, force_recommend

    def is_in_echo_cooldown(self, key: SessionKey | str) -> bool:
        self._cleanup(self._clock())
        if not key or not self.echo_cooldown_enabled:
            return False
        state = self._sessions.get(key)
        return state is not None and state.last_echo is not None

    def record_echo(self, key: SessionKey | str) -> None:
        now = self._clock()
        self._cleanup(now)
        if key and self.echo_cooldown_enabled and self.echo_cooldown_seconds > 0:
            self._state(key).last_echo = now

    def clear_all(self) -> None:
        self._sessions.clear()
