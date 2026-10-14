"""吃什么推荐插件。"""

__all__ = ["WhatToEatPlugin"]


def __getattr__(name: str) -> type:
    if name == "WhatToEatPlugin":
        from .main import WhatToEatPlugin

        return WhatToEatPlugin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
