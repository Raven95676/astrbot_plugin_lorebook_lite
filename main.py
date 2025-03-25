from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register("astrbot_plugin_lorebook_lite", "Raven95676", "lorebook插件", "0.1.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def terminate(self):
        """当插件被卸载/停用时会调用。"""
