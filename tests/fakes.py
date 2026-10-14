"""离线测试使用的最小 AstrBot 事件和数据目录接口。"""

from __future__ import annotations

import asyncio
import importlib
import logging
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch


@dataclass
class MessageResult:
    texts: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)

    def message(self, text: str) -> MessageResult:
        self.texts.append(text)
        return self

    def file_image(self, path: str) -> MessageResult:
        self.images.append(path)
        return self

    @property
    def text(self) -> str:
        return "".join(self.texts)


class FakeEvent:
    def __init__(
        self,
        text: str,
        *,
        platform: str = "qq-main",
        group: str = "100",
        sender: str = "12345",
        self_id: str = "99999",
        fail_send: bool = False,
    ) -> None:
        self.message_str = text
        self.message_obj = types.SimpleNamespace(self_id=self_id)
        self.platform = platform
        self.group = group
        self.sender = sender
        self.stopped = False
        self.call_llm = False
        self.sent: list[MessageResult] = []
        self.send_attempts = 0
        self.fail_send = fail_send

    def get_platform_id(self) -> str:
        return self.platform

    def get_group_id(self) -> str:
        return self.group

    def get_sender_id(self) -> str:
        return self.sender

    def is_stopped(self) -> bool:
        return self.stopped

    def stop_event(self) -> None:
        self.stopped = True

    def should_call_llm(self, value: bool) -> None:
        self.call_llm = value

    def plain_result(self, text: str) -> MessageResult:
        return MessageResult().message(text)

    def make_result(self) -> MessageResult:
        return MessageResult()

    async def send(self, result: MessageResult) -> None:
        if not self.stopped or not self.call_llm:
            raise AssertionError("发送前必须停止事件并禁止默认 LLM 回复")
        self.send_attempts += 1
        await asyncio.sleep(0)
        if self.fail_send:
            raise OSError("模拟平台发送失败")
        self.sent.append(result)


class FakeClock:
    def __init__(self, now: float = 0.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class FakeContext:
    pass


def import_entry():
    api = types.ModuleType("astrbot.api")
    api.AstrBotConfig = dict
    api.logger = logging.getLogger("what-to-eat-tests")
    event = types.ModuleType("astrbot.api.event")

    def event_message_type(message_type, **kwargs):
        def decorate(handler):
            handler._event_priority = kwargs.get("priority", 0)
            handler._event_message_type = message_type
            return handler

        return decorate

    event.AstrMessageEvent = FakeEvent
    event.filter = types.SimpleNamespace(
        EventMessageType=types.SimpleNamespace(ALL="all"),
        event_message_type=event_message_type,
    )
    star = types.ModuleType("astrbot.api.star")

    class Star:
        def __init__(self, context):
            self.context = context

    star.Context, star.Star = FakeContext, Star
    star_tools = types.ModuleType("astrbot.core.star.star_tools")

    class StarTools:
        @staticmethod
        def get_data_dir(plugin_name: str) -> Path:
            raise AssertionError("测试必须提供临时插件数据目录")

    star_tools.StarTools = StarTools
    modules = {
        "astrbot": types.ModuleType("astrbot"),
        "astrbot.api": api,
        "astrbot.api.event": event,
        "astrbot.api.star": star,
        "astrbot.core": types.ModuleType("astrbot.core"),
        "astrbot.core.star": types.ModuleType("astrbot.core.star"),
        "astrbot.core.star.star_tools": star_tools,
    }
    with patch.dict(sys.modules, modules):
        entry = importlib.import_module("astrbot_plugin_what_to_eat.main")
        plugin_modules = {
            name: module
            for name, module in sys.modules.items()
            if name.startswith("astrbot_plugin_what_to_eat.")
        }
    # 保留已加载的插件模块，同时恢复所有模拟的 AstrBot 名称。
    sys.modules.update(plugin_modules)
    return entry
