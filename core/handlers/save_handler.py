import json
import os
import re
from typing import TYPE_CHECKING

from astrbot.api import logger

if TYPE_CHECKING:
    from ..parser import LoreParser


class SaveHandler:
    """保存处理器类，用于处理保存和加载操作"""

    def __init__(self, parser: "LoreParser"):
        """初始化保存处理器

        Args:
            parser: 解析器实例，用于访问和修改变量数据
        """
        self.parser: "LoreParser" = parser
        self.data_path = os.path.join(os.getcwd(), "data", "lorebook_lite_saves")
        os.makedirs(
            self.data_path, exist_ok=True
        )  # 同步创建目录，因为这只在初始化时执行一次

    def _get_session_ps(self):
        """获取当前会话的安全文件名

        Returns:
            str: 处理后的会话ID，可用作文件名
        """
        return re.sub(r'[\\/:*?"<>|!]', "_", self.parser.session)

    def handle_save_oper(self, args: list[str]) -> str:
        """处理保存操作

        Args:
            args: 操作参数列表

        Returns:
            str: 操作结果消息
        """
        if not args:
            return "无参数"

        try:
            match args:
                case ["world"]:
                    self._save_world_state()
                    return "世界状态已保存"
                case ["user"]:
                    self._save_user_state()
                    return "用户状态已保存"
                case _:
                    return "未知参数"
        except Exception as e:
            logger.error(f"保存状态时出错: {e}")
            return f"保存失败: {str(e)}"

    def handle_load_oper(self, args: list[str]) -> str:
        """处理加载操作

        Args:
            args: 操作参数列表

        Returns:
            str: 操作结果消息
        """
        if not args:
            return "无参数"

        try:
            match args:
                case ["world"]:
                    result = self._load_world_state()
                    return result if result else "世界状态已加载"
                case ["user"]:
                    result = self._load_user_state()
                    return result if result else "用户状态已加载"
                case _:
                    return "未知参数"
        except Exception as e:
            logger.error(f"加载状态时出错: {e}")
            return f"加载失败: {str(e)}"

    def _save_world_state(self) -> None:
        """保存世界状态到文件"""
        try:
            world_state = self.parser._vars.get("world", {})
            if not world_state:
                logger.debug("世界状态为空，不保存")
                return

            session_ps = self._get_session_ps()
            filename = f"{session_ps}_world_state.json"
            filepath = os.path.join(self.data_path, filename)

            logger.debug(f"保存世界状态到: {filepath}")
            json_data = json.dumps(world_state, ensure_ascii=False, indent=2)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_data)
                f.flush()

        except Exception as e:
            logger.error(f"保存世界状态时出错: {e}")
            raise

    def _save_user_state(self) -> None:
        """保存用户状态到文件"""
        try:
            user_states = {}
            for key, value in self.parser._vars.items():
                if key != "world" and ":" in key:
                    user_states[key] = value

            if not user_states:
                logger.debug("用户状态为空，不保存")
                return

            session_ps = self._get_session_ps()
            filename = f"{session_ps}_user_state.json"
            filepath = os.path.join(self.data_path, filename)

            logger.debug(f"保存用户状态到: {filepath}")
            json_data = json.dumps(user_states, ensure_ascii=False, indent=2)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_data)
                f.flush()

        except Exception as e:
            logger.error(f"保存用户状态时出错: {e}")
            raise

    def _load_world_state(self) -> str:
        """加载世界状态"""
        try:
            session_ps = self._get_session_ps()
            filename = f"{session_ps}_world_state.json"
            filepath = os.path.join(self.data_path, filename)

            if not os.path.exists(filepath):
                return f"找不到世界状态文件: {filename}"

            logger.debug(f"从 {filepath} 加载世界状态")
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                world_state = json.loads(content)

            self.parser._vars["world"] = world_state
            return None

        except Exception as e:
            logger.error(f"加载世界状态时出错: {e}")
            raise

    def _load_user_state(self) -> str:
        """加载用户状态"""
        try:
            session_ps = self._get_session_ps()
            filename = f"{session_ps}_user_state.json"
            filepath = os.path.join(self.data_path, filename)

            if not os.path.exists(filepath):
                return f"找不到用户状态文件: {filename}"

            logger.debug(f"从 {filepath} 加载用户状态")
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                user_states = json.loads(content)

            for key, value in user_states.items():
                self.parser._vars[key] = value
            return None

        except Exception as e:
            logger.error(f"加载用户状态时出错: {e}")
            raise
