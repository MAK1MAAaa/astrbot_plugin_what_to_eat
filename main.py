"""吃什么推荐插件主文件。"""

from __future__ import annotations

import re
from pathlib import Path

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core.star.star_tools import StarTools

from .food_data import FoodDataManager
from .image_manager import ImageManager
from .rate_limiter import RateLimiter, SessionKey
from .responder import Responder

PLUGIN_NAME = "astrbot_plugin_what_to_eat"


class WhatToEatPlugin(Star):
    """按关键词随机推荐食物或复读，支持独立的频率保护和复读冷却。"""

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config
        raw_keywords = config.get("trigger_keywords", ["吃什么"])
        if not isinstance(raw_keywords, list):
            raw_keywords = []
        self.trigger_keywords = list(
            dict.fromkeys(
                keyword.strip()
                for keyword in raw_keywords
                if isinstance(keyword, str) and keyword.strip()
            )
        ) or ["吃什么"]
        self.keyword_pattern = re.compile(
            "|".join(re.escape(keyword) for keyword in self.trigger_keywords)
        )

        # 频率保护关闭时仍保留冷却状态，两个开关独立生效。
        self.rate_limiter = RateLimiter(
            max_responses=config.get("rate_limit_max", 3),
            window_seconds=config.get("rate_limit_window_seconds", 60),
            rate_limit_enabled=config.get("rate_limit_enabled", True),
            echo_cooldown_enabled=config.get("echo_cooldown_enabled", True),
            echo_cooldown_seconds=config.get("echo_cooldown_seconds", 15),
        )
        self.food_manager = FoodDataManager(config)
        self.responder = Responder(config.get("recommend_probability", 0.7))
        self.image_manager = ImageManager(
            config,
            Path(__file__).resolve().parent,
            StarTools.get_data_dir(PLUGIN_NAME),
        )
        image_count = sum(len(paths) for paths in self.image_manager.all_images.values())
        logger.info(
            f"吃什么插件初始化成功，关键词: {self.trigger_keywords}，已加载 {image_count} 张配图"
        )

    @staticmethod
    def _session_key(event: AstrMessageEvent) -> SessionKey:
        platform_id = str(event.get_platform_id())
        group_id = str(event.get_group_id() or "")
        if group_id:
            return platform_id, "group", group_id
        return platform_id, "private", str(event.get_sender_id())

    @filter.event_message_type(filter.EventMessageType.ALL, priority=0)
    async def on_what_to_eat(
        self, event: AstrMessageEvent, *args: object, **kwargs: object
    ) -> None:
        if event.is_stopped():
            return
        self_id = str(getattr(event.message_obj, "self_id", "") or "")
        if self_id and self_id == str(event.get_sender_id()):
            return
        message_text = event.message_str
        if not message_text or not self.keyword_pattern.search(message_text):
            return

        # 直接发送结果，避免 yield 新结果覆盖旧版框架的停止标记。
        event.should_call_llm(True)
        event.stop_event()
        try:
            key = self._session_key(event)
            _, force_recommend = self.rate_limiter.check_and_record(key)
            should_recommend = (
                force_recommend
                or self.rate_limiter.is_in_echo_cooldown(key)
                or self.responder.should_recommend()
            )
            if should_recommend:
                food = self.food_manager.get_random_food()
                response_text = self.responder.get_food_response(food)
                image_path = self.image_manager.get_random_image(food)
                if image_path:
                    result = (
                        event.make_result().message(response_text).file_image(image_path)
                    )
                else:
                    result = event.plain_result(response_text)
            else:
                # 必须在首次 await 前占位，同一会话的并发请求才能看见冷却。
                self.rate_limiter.record_echo(key)
                result = event.plain_result(self.responder.get_echo_response())
        except Exception:
            logger.exception("吃什么插件准备回复失败")
            result = event.plain_result("哎呀，出错了...")

        try:
            await event.send(result)
        except Exception:
            # 平台可能已经部分发送；不再补发，避免重复回复。
            logger.exception("吃什么插件发送回复失败")

    async def terminate(self) -> None:
        self.rate_limiter.clear_all()
        self.food_manager.clear_cache()
        logger.info("吃什么插件已终止")
