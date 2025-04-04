import copy
import random
import re
from collections import deque
from datetime import datetime
from typing import Any

from kwmatcher import AhoMatcher

from astrbot.api import logger

from ._types import LoreResult, Trigger  # type: ignore
from .handlers.logic_handler import LogicHandler  # type: ignore
from .handlers.random_handler import RandomHandler  # type: ignore
from .handlers.time_handler import TimeHandler  # type: ignore
from .handlers.var_handler import VarHandler  # type: ignore

# 定义占位符的正则表达式模式，用于匹配 {namespace::function(args)} 格式
PLACE_PATTERN = re.compile(r"\{([a-zA-Z0-9_]+)::([a-zA-Z0-9_]+)(?:\(([^(){}]*)\))?}")

# 定义最大递归深度
MAX_RECURSION_DEPTH = 25


class LoreParser:
    __slots__ = (
        "sender",
        "sender_name",
        "messages",
        "_lorebook",
        "_vars",
        "_triggers",
        "_notes",
        "_current_time",
        "_real_idle",
        "_world_idle",
        "_var_handler",
        "_time_handler",
        "_random_handler",
        "_logic_handler",
    )

    def __init__(self, lorebook: dict[str, Any], scan_depth: int = 1):
        """初始化Lorebook解析器

        Args:
            lorebook: Lorebook配置字典
            scan_depth: 扫描深度
        """
        self._lorebook = lorebook
        self.sender = "AstrBot"
        self.sender_name = "AstrBot"
        self.messages: deque[str] = deque(maxlen=scan_depth)

        # 初始化变量存储
        self._vars: dict[str, Any] = {}
        self._vars["world"] = copy.deepcopy(self._lorebook.get("world_state", {}))
        self._vars.update(
            {
                item["name"]: copy.deepcopy(item.get("variables", {}))
                for item in self._lorebook.get("user_state", [])
            }
        )
        # 设置当前时间，优先使用世界时间，否则使用系统时间
        if self._vars["world"].get("world_time") is not None:
            self._current_time = datetime.strptime(
                self._vars["world"]["world_time"], "%Y-%m-%d %H:%M"
            )
        else:
            self._current_time = datetime.now()

        self._real_idle: dict[str, datetime] = {
            "before": datetime.now(),
            "after": datetime.now(),
        }

        self._world_idle: dict[str, datetime] = {
            "before": self._current_time,
            "after": self._current_time,
        }

        # 按优先级排序触发器
        self._triggers: list[Trigger] = sorted(
            [
                Trigger(
                    name=t.get("name", ""),
                    type=t.get("type", "keywords"),
                    match=t.get("match"),
                    conditional=t.get("conditional"),
                    priority=t.get("priority", 0),
                    block=t.get("block", False),
                    probability=t.get("probability", 1.0),
                    use_logic=t.get("use_logic", True),
                    position=t.get("position", "sys_start"),
                    content=t.get("content", ""),
                    actions=t.get("actions", []),
                )
                for t in lorebook.get("trigger", [])
            ],
            key=lambda trigger: -trigger.priority,
        )

        # 初始化作者注释
        self._notes: list[Trigger] = [
            Trigger(
                content=note.get("content", ""),
                probability=note.get("probability", 1.0),
                position=note.get("position", "sys_start"),
            )
            for note in lorebook.get("authors_note", [])
        ]

        # 初始化各种处理器
        self._var_handler = VarHandler(self)
        self._time_handler = TimeHandler(self)
        self._random_handler = RandomHandler(self)
        self._logic_handler = LogicHandler(self)

    def __str__(self) -> str:
        """返回解析器的字符串表示"""
        return f"LoreParser(variables={self._vars},triggers={self._triggers},authors_notes={self._notes})"

    def __repr__(self) -> str:
        """返回解析器的官方字符串表示"""
        return self.__str__()

    def _parse_dict(self, d: Any) -> Any:
        """递归解析字典中所有键和值中的占位符

        Args:
            d: 要解析的字典或其他值

        Returns:
            解析后的字典或值
        """
        if not isinstance(d, dict):
            return self.parse_placeholder(str(d)) if isinstance(d, str) else d

        parsed_dict = {}
        for key, value in d.items():
            parsed_key = self.parse_placeholder(str(key))
            if isinstance(value, dict):
                parsed_value = self._parse_dict(value)
            elif isinstance(value, list):
                parsed_value = [
                    self._parse_dict(item)
                    if isinstance(item, dict)
                    else self.parse_placeholder(str(item))
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                parsed_value = (
                    self.parse_placeholder(str(value))
                    if isinstance(value, str)
                    else value
                )
            parsed_dict[parsed_key] = parsed_value
        return parsed_dict

    def parse_placeholder(self, text: str) -> str:
        """解析文本中的占位符，支持多阶段解析

        Args:
            text: 包含占位符的文本

        Returns:
            解析后的文本
        """
        if not isinstance(text, str):
            return str(text)

        def replace_match(match, phase):
            """根据不同阶段处理匹配到的占位符

            Args:
                match: 正则表达式匹配对象
                phase: 处理阶段(1-3)

            Returns:
                替换后的文本
            """
            try:
                namespace = match.group(1)
                function = match.group(2)
                args_str = match.group(3) or ""

                args = self._split_args(args_str) if args_str else []

                match (phase, namespace, function):
                    # 阶段1: 处理基础内置函数
                    case (1, "buildin", "sender"):
                        return self.sender
                    case (1, "buildin", "sender_name"):
                        return self.sender_name
                    case (1, "buildin", "time"):
                        return self._time_handler.handle_time_oper(args)
                    case (1, "buildin", "random"):
                        return self._random_handler.handle_random_oper(args)

                    # 阶段2: 处理变量设置
                    case (2, "var", "set"):
                        return self._var_handler.handle_var_oper(function, args)

                    # 阶段3: 处理所有其他函数
                    case (3, "var", _):
                        return self._var_handler.handle_var_oper(function, args)
                    case (3, "logic", _):
                        return self._logic_handler.handle_logic_oper(function, args)

                # 默认情况：保持原样
                return match.group(0)
            except Exception as e:
                logger.debug(f"解析占位符时出现错误: {e!s}, 占位符: {match.group(0)}")
                return match.group(0)

        # 阶段1: 处理基础内置函数
        for _ in range(MAX_RECURSION_DEPTH):
            new_text = PLACE_PATTERN.sub(lambda m: replace_match(m, phase=1), text)
            if new_text == text:  # 如果文本没有变化，跳出循环
                break
            text = new_text

        # 阶段2: 处理变量设置
        for _ in range(MAX_RECURSION_DEPTH):
            new_text = PLACE_PATTERN.sub(lambda m: replace_match(m, phase=2), text)
            if new_text == text:
                break
            text = new_text

        # 阶段3: 处理所有其他函数
        for _ in range(MAX_RECURSION_DEPTH):
            new_text = PLACE_PATTERN.sub(lambda m: replace_match(m, phase=3), text)
            if new_text == text:
                break
            text = new_text

        return text

    def _split_args(self, args_str: str) -> list[str]:
        """切分参数字符串，支持引号保护。

        Args:
            args_str: 参数字符串，如 'a, "b,c", d'

        Returns:
            参数列表，如 ['a', 'b,c', 'd']
        """
        args = []
        current: list[str] = []
        in_quotes = False
        quote_char = None

        args_str = args_str.strip()
        if args_str.startswith("[") and args_str.endswith("]"):
            args_str = args_str[1:-1]

        for c in args_str:
            if c in "\"'" and not in_quotes:
                in_quotes = True
                quote_char = c
            elif c == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif c == "," and not in_quotes:
                args.append("".join(current).strip())
                current = []
            else:
                current.append(c)

        # 确保添加最后一个参数
        if current:
            args.append("".join(current).strip())

        # 如果解析结束时仍在引号内，记录警告
        if in_quotes:
            logger.warning(f"引号不匹配: {args_str}")

        # 移除每个参数可能残留的首尾引号
        for i in range(len(args)):
            arg = args[i]
            if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                args[i] = arg[1:-1]

        return args

    def _can_trigger(self, trigger: Trigger, messages: deque[str]) -> bool:
        """检查触发器是否可以触发

        Args:
            trigger: 要检查的触发器对象
            messages: 消息列表

        Returns:
            布尔值，表示触发器是否可以触发
        """
        # 检查概率条件
        if random.random() > trigger.probability:
            return False

        # 检查条件表达式
        if trigger.conditional:
            parsed_condition = self.parse_placeholder(trigger.conditional)
            if not self._logic_handler._eval_cond(parsed_condition):
                return False

        # 检查消息匹配条件
        for message in messages:
            # 正则表达式匹配
            if trigger.type == "regex" and trigger.match:
                try:
                    if bool(re.search(trigger.match, message)):
                        return True
                except re.error as e:
                    logger.warning(f"无效的正则表达式: {trigger.match}, 错误: {e}")
                    continue
            # 关键词匹配
            elif trigger.type == "keywords" and trigger.match:
                try:
                    matcher = AhoMatcher(use_logic=trigger.use_logic)
                    keywords = self._split_args(trigger.match)
                    matcher.build(set(keywords))
                    if bool(matcher.find(message)):
                        return True
                except Exception as e:
                    logger.warning(f"关键词匹配器错误: {e}, 关键词: {trigger.match}")
                    continue
            # 监听器类型触发器总是触发
            elif trigger.type == "listener":
                return True
        return False  # 没有匹配任何条件

    def _process_trigger(
        self,
        trigger: Trigger,
        messages: deque[str],
        result: LoreResult,
        depth: int = 1,
        skip_chk: bool = False,
    ) -> bool:
        """处理触发器，执行相应操作并更新结果

        Args:
            trigger: 触发器
            messages: 消息列表
            result: 结果对象，用于存储处理结果
            depth: 当前递归深度，防止无限递归
            skip_chk: 是否跳过触发条件检查

        Returns:
            布尔值，表示是否应该继续处理下一个触发器
        """
        # 防止递归过深
        if depth > MAX_RECURSION_DEPTH:
            return False

        # 检查触发条件（除非跳过检查）
        can_trigger = True
        if not skip_chk:
            can_trigger = self._can_trigger(trigger, messages)
            if not can_trigger:
                return True  # 继续处理下一个触发器

        # 解析触发器内容并根据位置添加到结果中
        content = self.parse_placeholder(trigger.content)
        if trigger.position == "sys_start":
            result.sys_start.append(content)
        elif trigger.position == "sys_end":
            result.sys_end.append(content)
        elif trigger.position == "user_start":
            result.user_start.append(content)
        elif trigger.position == "user_end":
            result.user_end.append(content)

        for action in trigger.actions:
            parsed_action = self.parse_placeholder(action)
            # 如果动作是另一个触发器的名称，则递归处理该触发器
            trigger_by_name = next((t for t in self._triggers if t.name == parsed_action), None)
            if trigger_by_name and parsed_action != trigger.name:  # 防止自我递归
                self._process_trigger(
                    trigger_by_name, messages, result, depth + 1, True
                )

        return not trigger.block if can_trigger else True

    def process_chat(self) -> LoreResult:
        """处理聊天消息，应用所有适用的触发器和注释

        Args:
            messages: 消息列表

        Returns:
            LoreResult对象，包含处理后的各位置内容
        """
        result = LoreResult()
        triged_lis: set[str] = set()
        # 更新真实世界的空闲时间
        self._real_idle["before"] = self._real_idle["after"]
        self._real_idle["after"] = datetime.now()

        # 处理所有触发器
        for trigger in self._triggers:
            # 特殊处理监听器类型触发器，确保每个只触发一次
            if trigger.type == "listener":
                if trigger.name in triged_lis:
                    continue
                else:
                    triged_lis.add(trigger.name)
            # 处理当前触发器, 如果返回 False，则停止处理下一个触发器
            if not self._process_trigger(trigger, self.messages, result):
                break

        # 处理作者注释
        for note in self._notes:
            if random.random() < note.probability:
                content = self.parse_placeholder(note.content)
                # 根据位置添加到结果中
                if note.position == "sys_start":
                    result.sys_start.append(content)
                elif note.position == "user_start":
                    result.user_start.append(content)
                elif note.position == "sys_end":
                    result.sys_end.append(content)
                elif note.position == "user_end":
                    result.user_end.append(content)

        return result
