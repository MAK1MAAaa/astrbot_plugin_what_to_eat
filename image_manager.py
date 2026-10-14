"""食物配图管理，兼容上传文件、旧上传路径和手工 images 目录。"""

from __future__ import annotations

import os
import random
import re
from pathlib import Path
from typing import TYPE_CHECKING

from astrbot.api import logger

if TYPE_CHECKING:
    from astrbot.api import AstrBotConfig

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"})


class ImageManager:
    def __init__(
        self,
        config: AstrBotConfig,
        plugin_dir: str | Path,
        data_dir: str | Path | None = None,
    ) -> None:
        self.config = config
        self.plugin_dir = Path(plugin_dir).resolve()
        self.data_dir = (
            Path(data_dir).resolve() if data_dir is not None else self.plugin_dir
        )
        self.images_dir = self.plugin_dir / "images"
        self.scanned_images = self._scan_images_folder()
        self.config_images = self._scan_config_images()
        self.all_images = self._merge_images(self.scanned_images, self.config_images)

    @staticmethod
    def _is_image_file(path: Path) -> bool:
        try:
            return (
                path.suffix.lower() in IMAGE_EXTENSIONS
                and path.is_file()
                and os.access(path, os.R_OK)
            )
        except OSError:
            return False

    @staticmethod
    def _extract_food_name(filename: str) -> str | None:
        name = re.sub(r"[_-]\d+$", "", Path(filename).stem).strip()
        return name or None

    def _scan_images_folder(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        try:
            if not self.images_dir.is_dir():
                return result
            for path in self.images_dir.iterdir():
                if not self._is_image_file(path):
                    continue
                food_name = self._extract_food_name(path.name)
                if food_name:
                    result.setdefault(food_name, []).append(str(path.resolve()))
        except OSError:
            logger.exception("扫描食物图片目录失败，继续使用文字推荐")
        for paths in result.values():
            paths.sort()
        return result

    def _get_full_path(self, filepath: str) -> str | None:
        path = Path(filepath.replace("\\", "/"))
        try:
            if path.is_absolute():
                return str(path.resolve())
            if ".." in path.parts:
                return None
            # 新版 WebUI 保存到 plugin_data；已存在的旧文件继续从插件目录读取。
            candidates = [self.data_dir / path, self.plugin_dir / path]
            for candidate in candidates:
                resolved = candidate.resolve()
                if self._is_image_file(resolved):
                    return str(resolved)
        except (OSError, ValueError, RuntimeError):
            return None
        return None

    def _scan_config_images(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        uploaded_images = self.config.get("uploaded_images", [])
        if not isinstance(uploaded_images, list):
            return result
        for filepath in uploaded_images:
            if not isinstance(filepath, str) or not filepath.strip():
                continue
            full_path = self._get_full_path(filepath.strip())
            if not full_path or not self._is_image_file(Path(full_path)):
                continue
            food_name = self._extract_food_name(
                Path(filepath.strip().replace("\\", "/")).name
            )
            if food_name:
                result.setdefault(food_name, []).append(full_path)
        return result

    @staticmethod
    def _merge_images(
        scanned: dict[str, list[str]], configured: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        # 复制列表，避免合并时把配置图片写回扫描结果。
        result = {food: list(paths) for food, paths in scanned.items()}
        for food, paths in configured.items():
            result.setdefault(food, []).extend(paths)
        return {food: sorted(set(paths)) for food, paths in result.items()}

    def get_random_image(self, food_name: str | None) -> str | None:
        if not food_name:
            return None
        paths = self.all_images.get(food_name.strip(), [])
        existing = [path for path in paths if self._is_image_file(Path(path))]
        return random.choice(existing) if existing else None

    def has_images(self, food_name: str) -> bool:
        return any(
            self._is_image_file(Path(path))
            for path in self.all_images.get(food_name.strip(), [])
        )

    def get_all_foods_with_images(self) -> list[str]:
        return [food for food in self.all_images if self.has_images(food)]

    def reload(self) -> None:
        self.scanned_images = self._scan_images_folder()
        self.config_images = self._scan_config_images()
        self.all_images = self._merge_images(self.scanned_images, self.config_images)
