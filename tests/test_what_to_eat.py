from __future__ import annotations

import ast
import asyncio
import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from astrbot_plugin_what_to_eat.tests.fakes import (
    FakeClock,
    FakeContext,
    FakeEvent,
    import_entry,
)

ENTRY = import_entry()

from astrbot_plugin_what_to_eat.food_data import DEFAULT_FOODS, FoodDataManager
from astrbot_plugin_what_to_eat.image_manager import ImageManager
from astrbot_plugin_what_to_eat.rate_limiter import RateLimiter
from astrbot_plugin_what_to_eat.responder import Responder

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
)


def image_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PNG)
    return path.resolve()


class FoodAndReplyTests(unittest.TestCase):
    def test_package_keeps_upstream_entry_class_export(self):
        from astrbot_plugin_what_to_eat import WhatToEatPlugin

        self.assertIs(WhatToEatPlugin, ENTRY.WhatToEatPlugin)

    def test_default_foods_match_schema(self):
        schema = json.loads((PLUGIN_ROOT / "_conf_schema.json").read_text())
        self.assertEqual(len(DEFAULT_FOODS), 50)
        self.assertEqual(list(DEFAULT_FOODS), schema["builtin_foods"]["default"])
        self.assertEqual(FoodDataManager({}).get_all_foods(), list(DEFAULT_FOODS))
        self.assertEqual(Responder().probability, schema["recommend_probability"]["default"])

    def test_lists_are_cleaned_and_deduplicated(self):
        manager = FoodDataManager(
            {
                "builtin_foods": [" 水饺 ", "", None, 3, "炒饭", "水饺"],
                "custom_foods": ["炒饭", " 麻辣烫 "],
            }
        )
        self.assertEqual(manager.get_all_foods(), ["水饺", "炒饭", "麻辣烫"])
        with patch(
            "astrbot_plugin_what_to_eat.food_data.random.choice", return_value="麻辣烫"
        ) as choose:
            self.assertEqual(manager.get_random_food(), "麻辣烫")
            choose.assert_called_once_with(["水饺", "炒饭", "麻辣烫"])

    def test_empty_library_remains_empty(self):
        manager = FoodDataManager({"builtin_foods": [], "custom_foods": []})
        self.assertFalse(manager.has_foods())
        self.assertIsNone(manager.get_random_food())
        self.assertEqual(Responder().get_food_response(None), Responder().get_fallback_response())

    def test_single_string_food_and_invalid_list_values(self):
        manager = FoodDataManager({"builtin_foods": " 水饺 ", "custom_foods": {"bad": 1}})
        self.assertEqual(manager.get_all_foods(), ["水饺"])
        manager = FoodDataManager({"builtin_foods": None, "custom_foods": [False, " "]})
        self.assertEqual(manager.get_all_foods(), [])

    def test_probability_edges_and_threshold(self):
        with patch("astrbot_plugin_what_to_eat.responder.random.random", return_value=0.0):
            self.assertFalse(Responder(0).should_recommend())
            self.assertTrue(Responder(1).should_recommend())
        with patch("astrbot_plugin_what_to_eat.responder.random.random", return_value=0.7):
            self.assertFalse(Responder().should_recommend())
        with patch("astrbot_plugin_what_to_eat.responder.random.random", return_value=0.699):
            self.assertTrue(Responder().should_recommend())
        self.assertEqual(Responder(-1).probability, 0)
        self.assertEqual(Responder(2).probability, 1)

    def test_invalid_probabilities_fall_back(self):
        for value in (None, True, "bad", float("nan"), float("inf"), []):
            with self.subTest(value=value):
                self.assertEqual(Responder(value).probability, 0.7)
        self.assertEqual(Responder("0.5").probability, 0.5)

    def test_food_text_is_formatted_as_data(self):
        for template in Responder.RECOMMEND_TEMPLATES:
            with patch("astrbot_plugin_what_to_eat.responder.random.choice", return_value=template):
                self.assertIn("水饺{调料}", Responder().get_food_response("水饺{调料}"))
        self.assertEqual(Responder().get_echo_response(), "是啊，吃什么")


class RateLimiterTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.key = ("qq-main", "group", "100")
        self.limiter = RateLimiter(clock=self.clock)

    def test_fourth_response_is_forced_and_window_expires(self):
        for _ in range(3):
            self.assertEqual(self.limiter.check_and_record(self.key), (True, False))
        self.assertEqual(self.limiter.check_and_record(self.key), (True, True))
        self.clock.now = 60
        self.assertEqual(self.limiter.check_and_record(self.key), (True, False))

    def test_window_is_sliding_and_timestamps_are_bounded(self):
        self.limiter.check_and_record(self.key)
        self.clock.now = 50
        for _ in range(2):
            self.limiter.check_and_record(self.key)
        self.clock.now = 60
        self.assertEqual(self.limiter.check_and_record(self.key), (True, False))
        for _ in range(100):
            self.assertEqual(self.limiter.check_and_record(self.key), (True, True))
        self.assertEqual(len(self.limiter._sessions[self.key].responses), 3)

    def test_cooldown_includes_timestamp_zero_and_expires_at_boundary(self):
        self.limiter.record_echo(self.key)
        self.assertTrue(self.limiter.is_in_echo_cooldown(self.key))
        self.clock.now = 14.999
        self.assertTrue(self.limiter.is_in_echo_cooldown(self.key))
        self.clock.now = 15
        self.assertFalse(self.limiter.is_in_echo_cooldown(self.key))

    def test_rate_limit_can_be_disabled_without_disabling_cooldown(self):
        limiter = RateLimiter(rate_limit_enabled=False, clock=self.clock)
        for _ in range(5):
            self.assertEqual(limiter.check_and_record(self.key), (True, False))
        limiter.record_echo(self.key)
        self.assertTrue(limiter.is_in_echo_cooldown(self.key))
        self.assertEqual(len(limiter._sessions[self.key].responses), 0)

    def test_cooldown_can_be_disabled_without_disabling_rate_limit(self):
        limiter = RateLimiter(echo_cooldown_enabled=False, max_responses=1, clock=self.clock)
        limiter.record_echo(self.key)
        self.assertFalse(limiter.is_in_echo_cooldown(self.key))
        self.assertEqual(limiter.check_and_record(self.key), (True, False))
        self.assertEqual(limiter.check_and_record(self.key), (True, True))

    def test_zero_cooldown_and_empty_session_do_not_store_echoes(self):
        limiter = RateLimiter(echo_cooldown_seconds=0, clock=self.clock)
        limiter.record_echo(self.key)
        self.assertFalse(limiter.is_in_echo_cooldown(self.key))
        self.assertEqual(limiter.check_and_record(""), (True, False))
        limiter.record_echo("")
        self.assertEqual(len(limiter._sessions), 0)

    def test_expired_inactive_sessions_are_cleaned_on_other_activity(self):
        self.limiter.check_and_record(self.key)
        self.limiter.record_echo(self.key)
        self.clock.now = 60
        self.limiter.check_and_record(("qq-main", "group", "200"))
        self.assertNotIn(self.key, self.limiter._sessions)

    def test_session_count_is_bounded_and_unload_clears_it(self):
        limiter = RateLimiter(max_entries=2, max_responses=1, clock=self.clock)
        keys = [("qq-main", "group", str(index)) for index in range(3)]
        for key in keys[:2]:
            limiter.check_and_record(key)
        limiter.check_and_record(keys[0])
        limiter.check_and_record(keys[2])
        self.assertEqual(limiter.can_respond(keys[0]), (True, True))
        self.assertEqual(limiter.can_respond(keys[1]), (True, False))
        self.assertEqual(len(limiter._sessions), 2)
        limiter.clear_all()
        self.assertEqual(len(limiter._sessions), 0)

    def test_invalid_configuration_uses_valid_defaults(self):
        limiter = RateLimiter(
            max_responses="bad", window_seconds=True, echo_cooldown_seconds=None,
            rate_limit_enabled="false", echo_cooldown_enabled=0,
        )
        self.assertEqual(
            (limiter.max_responses, limiter.window_seconds, limiter.echo_cooldown_seconds),
            (3, 60, 15),
        )
        self.assertTrue(limiter.rate_limit_enabled)
        self.assertTrue(limiter.echo_cooldown_enabled)
        self.assertEqual(RateLimiter(max_responses=0, window_seconds=-1).window_seconds, 1)
        self.assertEqual(RateLimiter(echo_cooldown_seconds=-1).echo_cooldown_seconds, 0)
        self.assertEqual(RateLimiter(echo_cooldown_seconds=9999).echo_cooldown_seconds, 3600)


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.plugin_dir = self.root / "plugin"
        self.data_dir = self.root / "data"
        self.plugin_dir.mkdir()
        self.data_dir.mkdir()

    def manager(self, paths=None):
        return ImageManager({"uploaded_images": paths or []}, self.plugin_dir, self.data_dir)

    def test_manual_images_use_exact_food_name_and_multiple_numbered_files(self):
        first = image_file(self.plugin_dir / "images" / "水饺.png")
        second = image_file(self.plugin_dir / "images" / "水饺_2.PNG")
        third = image_file(self.plugin_dir / "images" / "水饺-3.png")
        image_file(self.plugin_dir / "images" / "水饺说明.txt")
        (self.plugin_dir / "images" / "水饺_4.png").mkdir()
        manager = self.manager()
        expected = sorted(map(str, (first, second, third)))
        self.assertEqual(manager.all_images, {"水饺": expected})
        with patch(
            "astrbot_plugin_what_to_eat.image_manager.random.choice",
            side_effect=lambda paths: paths[-1],
        ) as choose:
            self.assertEqual(manager.get_random_image(" 水饺 "), expected[-1])
            choose.assert_called_once_with(expected)
        self.assertIsNone(manager.get_random_image("水饺说明"))

    def test_uploads_are_resolved_from_data_directory_first(self):
        relative = "files/uploaded_images/水饺_1.png"
        current = image_file(self.data_dir / relative)
        image_file(self.plugin_dir / relative)
        manager = self.manager([relative])
        self.assertEqual(manager.get_random_image("水饺"), str(current))

    def test_legacy_upload_path_and_absolute_path_are_supported(self):
        relative = "files/uploaded_images/炒饭.png"
        legacy = image_file(self.plugin_dir / relative)
        absolute = image_file(self.data_dir / "files" / "uploaded_images" / "水饺.png")
        manager = self.manager([relative, str(absolute)])
        self.assertEqual(manager.get_random_image("炒饭"), str(legacy))
        self.assertEqual(manager.get_random_image("水饺"), str(absolute))

    def test_configured_symlink_name_is_used_for_food_binding(self):
        actual = image_file(self.data_dir / "shared" / "original.png")
        link = self.data_dir / "files" / "uploaded_images" / "水饺_1.png"
        link.parent.mkdir(parents=True)
        link.symlink_to(actual)
        manager = self.manager(["files/uploaded_images/水饺_1.png"])
        self.assertEqual(manager.get_random_image("水饺"), str(actual))
        self.assertIsNone(manager.get_random_image("original"))

    def test_merging_deduplicates_without_mutating_scan_results(self):
        manual = image_file(self.plugin_dir / "images" / "水饺.png")
        upload = image_file(self.data_dir / "files" / "uploaded_images" / "水饺_1.png")
        manager = self.manager([str(manual), str(upload), str(upload)])
        self.assertEqual(manager.scanned_images["水饺"], [str(manual)])
        self.assertEqual(manager.all_images["水饺"], sorted([str(manual), str(upload)]))

    def test_invalid_missing_unsupported_and_traversing_paths_are_ignored(self):
        image_file(self.root / "水饺.png")
        image_file(self.data_dir / "files" / "水饺.txt")
        manager = self.manager([None, 3, " ", "files/missing.png", "files/水饺.txt", "../水饺.png"])
        self.assertEqual(manager.all_images, {})
        self.assertIsNone(manager.get_random_image(None))
        invalid = ImageManager(
            {"uploaded_images": "bad"}, self.plugin_dir, self.data_dir
        )
        self.assertEqual(invalid.all_images, {})

    def test_deleted_files_are_skipped_and_reload_finds_new_images(self):
        path = image_file(self.plugin_dir / "images" / "水饺.png")
        manager = self.manager()
        path.unlink()
        self.assertIsNone(manager.get_random_image("水饺"))
        self.assertFalse(manager.has_images("水饺"))
        self.assertEqual(manager.get_all_foods_with_images(), [])
        replacement = image_file(self.plugin_dir / "images" / "炒饭_1.png")
        manager.reload()
        self.assertEqual(manager.get_random_image("炒饭"), str(replacement))

    def test_unreadable_image_is_not_selected(self):
        image_file(self.plugin_dir / "images" / "水饺.png")
        with patch("astrbot_plugin_what_to_eat.image_manager.os.access", return_value=False):
            self.assertEqual(self.manager().all_images, {})


class EntryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data_dir = Path(self.temporary.name)
        self.clock = FakeClock()

    def plugin(self, **config):
        with patch.object(ENTRY.StarTools, "get_data_dir", return_value=self.data_dir) as directory:
            plugin = ENTRY.WhatToEatPlugin(FakeContext(), config)
            directory.assert_called_once_with("astrbot_plugin_what_to_eat")
        plugin.rate_limiter._clock = self.clock
        return plugin

    async def reply(self, plugin, text="今天中午吃什么？", **kwargs):
        event = FakeEvent(text, **kwargs)
        await plugin.on_what_to_eat(event)
        self.assertTrue(event.stopped)
        self.assertTrue(event.call_llm)
        self.assertEqual(event.send_attempts, 1)
        self.assertEqual(len(event.sent), 1)
        return event.sent[0]

    async def test_contains_keyword_without_wake_requirements(self):
        plugin = self.plugin(recommend_probability=1, builtin_foods=["水饺"])
        for text in ("吃什么", "今天吃什么好？", "/吃什么", "  吃什么  "):
            result = await self.reply(plugin, text)
            self.assertIn("水饺", result.text)
            self.assertEqual(result.images, [])

    async def test_default_probability_uses_70_percent_threshold(self):
        plugin = self.plugin(
            builtin_foods=["水饺"],
            rate_limit_enabled=False,
            echo_cooldown_enabled=False,
        )
        with patch(
            "astrbot_plugin_what_to_eat.responder.random.random",
            side_effect=[0.699, 0.7],
        ):
            self.assertIn("水饺", (await self.reply(plugin)).text)
            self.assertEqual((await self.reply(plugin)).text, "是啊，吃什么")

    async def test_unrelated_self_and_stopped_events_are_untouched(self):
        plugin = self.plugin()
        events = [FakeEvent("晚安"), FakeEvent("吃什么", sender="99999"), FakeEvent("")]
        stopped = FakeEvent("吃什么")
        stopped.stop_event()
        events.append(stopped)
        for event in events:
            await plugin.on_what_to_eat(event)
            self.assertEqual(event.send_attempts, 0)
            self.assertFalse(event.call_llm)
        self.assertFalse(events[0].stopped)
        self.assertEqual(len(plugin.rate_limiter._sessions), 0)

    async def test_custom_keywords_are_trimmed_and_regex_characters_are_literal(self):
        plugin = self.plugin(
            trigger_keywords=[" 吃啥 ", "foo.*", "吃啥", " ", 3],
            recommend_probability=1,
            builtin_foods=["水饺"],
        )
        self.assertEqual(plugin.trigger_keywords, ["吃啥", "foo.*"])
        await self.reply(plugin, "吃啥好呢")
        await self.reply(plugin, "foo.*")
        ignored = FakeEvent("fooABC")
        await plugin.on_what_to_eat(ignored)
        self.assertFalse(ignored.stopped)

    async def test_invalid_keyword_lists_use_default(self):
        for keywords in ([], None, "吃啥", [False, " "]):
            with self.subTest(keywords=keywords):
                plugin = self.plugin(
                    trigger_keywords=keywords,
                    recommend_probability=1,
                    builtin_foods=["水饺"],
                )
                self.assertEqual(plugin.trigger_keywords, ["吃什么"])
                await self.reply(plugin)

    async def test_default_cooldown_forces_food_and_then_expires(self):
        plugin = self.plugin(
            recommend_probability=0, builtin_foods=["水饺"], rate_limit_enabled=False
        )
        self.assertEqual((await self.reply(plugin)).text, "是啊，吃什么")
        self.assertIn("水饺", (await self.reply(plugin)).text)
        self.clock.now = 15
        self.assertEqual((await self.reply(plugin)).text, "是啊，吃什么")

    async def test_fourth_response_is_forced_with_cooldown_disabled(self):
        plugin = self.plugin(
            recommend_probability=0, builtin_foods=["水饺"], echo_cooldown_enabled=False
        )
        for _ in range(3):
            self.assertEqual((await self.reply(plugin)).text, "是啊，吃什么")
        self.assertIn("水饺", (await self.reply(plugin)).text)
        self.clock.now = 60
        self.assertEqual((await self.reply(plugin)).text, "是啊，吃什么")

    async def test_both_guards_disabled_allow_repeated_echoes(self):
        plugin = self.plugin(
            recommend_probability=0,
            rate_limit_enabled=False,
            echo_cooldown_enabled=False,
        )
        for _ in range(5):
            self.assertEqual((await self.reply(plugin)).text, "是啊，吃什么")
        self.assertEqual(len(plugin.rate_limiter._sessions), 0)

    async def test_platforms_groups_and_private_senders_are_isolated(self):
        plugin = self.plugin(
            recommend_probability=0, builtin_foods=["水饺"], rate_limit_enabled=False
        )
        self.assertEqual((await self.reply(plugin, group="100")).text, "是啊，吃什么")
        self.assertIn("水饺", (await self.reply(plugin, group="100", sender="other")).text)
        second_platform = await self.reply(plugin, platform="qq-second", group="100")
        self.assertEqual(second_platform.text, "是啊，吃什么")
        self.assertEqual((await self.reply(plugin, group="200")).text, "是啊，吃什么")
        self.assertEqual((await self.reply(plugin, group="", sender="100")).text, "是啊，吃什么")
        self.assertIn("水饺", (await self.reply(plugin, group="", sender="100")).text)
        self.assertEqual((await self.reply(plugin, group="", sender="200")).text, "是啊，吃什么")

    async def test_concurrent_requests_reserve_echo_before_send(self):
        plugin = self.plugin(
            recommend_probability=0, builtin_foods=["水饺"], rate_limit_enabled=False
        )
        results = await asyncio.gather(*(self.reply(plugin) for _ in range(8)))
        self.assertEqual(sum(result.text == "是啊，吃什么" for result in results), 1)
        self.assertEqual(sum("水饺" in result.text for result in results), 7)

    async def test_empty_food_library_uses_upstream_fallback(self):
        plugin = self.plugin(recommend_probability=1, builtin_foods=[], custom_foods=[])
        result = await self.reply(plugin)
        self.assertEqual(result.text, "我想不到推荐什么...你自己决定吧！")
        self.assertEqual(result.images, [])

    async def test_upload_picture_is_sent_with_food_in_one_result(self):
        relative = "files/uploaded_images/水饺.png"
        path = image_file(self.data_dir / relative)
        plugin = self.plugin(
            recommend_probability=1, builtin_foods=["水饺"], uploaded_images=[relative]
        )
        result = await self.reply(plugin)
        self.assertIn("水饺", result.text)
        self.assertEqual(result.images, [str(path)])
        path.unlink()
        self.assertEqual((await self.reply(plugin)).images, [])

    async def test_echo_does_not_look_up_a_picture(self):
        plugin = self.plugin(recommend_probability=0)
        with patch.object(
            plugin.image_manager,
            "get_random_image",
            side_effect=AssertionError("复读不应查配图"),
        ):
            result = await self.reply(plugin)
        self.assertEqual(result.text, "是啊，吃什么")
        self.assertEqual(result.images, [])

    async def test_preparation_failure_sends_one_fixed_error(self):
        plugin = self.plugin(recommend_probability=1)
        with patch.object(plugin.food_manager, "get_random_food", side_effect=ValueError("模拟数据错误")):
            with self.assertLogs("what-to-eat-tests", level="ERROR"):
                result = await self.reply(plugin)
        self.assertEqual(result.text, "哎呀，出错了...")

    async def test_send_failure_is_logged_without_retry(self):
        plugin = self.plugin(recommend_probability=1)
        event = FakeEvent("吃什么", fail_send=True)
        with self.assertLogs("what-to-eat-tests", level="ERROR"):
            await plugin.on_what_to_eat(event)
        self.assertTrue(event.stopped)
        self.assertTrue(event.call_llm)
        self.assertEqual(event.send_attempts, 1)
        self.assertEqual(event.sent, [])

    async def test_existing_1d_handler_keeps_precedence(self):
        choice_root = PLUGIN_ROOT.parent / "astrbot_plugin_1d_choice"
        if not (choice_root / "main.py").is_file() or not (
            choice_root / "tests" / "fakes.py"
        ).is_file():
            self.skipTest("需要同目录下的 1d 选择插件及其测试资源")

        from astrbot_plugin_1d_choice.tests.fakes import (
            FakeContext as ChoiceContext,
            FakeEvent as ChoiceEvent,
            import_entry as import_choice,
        )

        source = (choice_root / "main.py").read_text()
        tree = ast.parse(source)
        handler = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "on_message"
        )
        priority = next(
            keyword.value.value for keyword in handler.decorator_list[0].keywords
            if keyword.arg == "priority"
        )
        self.assertGreater(priority, ENTRY.WhatToEatPlugin.on_what_to_eat._event_priority)
        choice_entry = import_choice()
        choice_plugin = choice_entry.OneDChoicePlugin(ChoiceContext(), {})
        event = ChoiceEvent("1d吃什么还是水饺")
        event.message_str = "1d吃什么还是水饺"
        event.is_stopped = lambda: event.stopped
        requests = [request async for request in choice_plugin.on_message(event)]
        self.assertEqual(requests, [])
        self.assertTrue(event.stopped)
        self.assertEqual(len(event.sent), 1)
        self.assertIn(event.sent[0], ("吃什么", "水饺"))
        food_plugin = self.plugin(recommend_probability=1)
        await food_plugin.on_what_to_eat(event)
        self.assertEqual(len(event.sent), 1)
        self.assertEqual(len(food_plugin.rate_limiter._sessions), 0)

    async def test_handler_accepts_framework_extra_arguments_and_unload_clears_state(self):
        plugin = self.plugin(recommend_probability=0)
        event = FakeEvent("吃什么")
        await plugin.on_what_to_eat(event, "extra", invocation="framework")
        self.assertEqual(event.send_attempts, 1)
        self.assertGreater(len(plugin.rate_limiter._sessions), 0)
        await plugin.terminate()
        self.assertEqual(len(plugin.rate_limiter._sessions), 0)


if __name__ == "__main__":
    unittest.main()
