import random
import re
from typing import TYPE_CHECKING

from astrbot.api import logger

if TYPE_CHECKING:
    from ..parser import LoreParser

# 骰子表示法的正则表达式
DICE_PATTERN = re.compile(r"([+-]?\d*d\d+(?:[kubrtl]\d+|adv|dis)?)|([+-]?\d+)")
ADV_PATTERN = re.compile(r"(\d*)d(\d+)adv")
DIS_PATTERN = re.compile(r"(\d*)d(\d+)dis")


class RandomHandler:
    """随机数处理器类，用于处理各种随机数生成操作"""

    def __init__(self, parser: "LoreParser"):
        """初始化随机数处理器

        Args:
            parser: 解析器实例，用于访问解析上下文
        """
        self.parser: "LoreParser" = parser

    def handle_random_oper(self, args: list[str]) -> str:
        """处理随机数相关操作

        Args:
            args: 操作参数列表

        Returns:
            随机操作的结果字符串
        """
        match args:
            # 处理两个数字参数的情况，生成指定范围内的随机整数
            case [a, b] if self._is_num(a) and self._is_num(b):
                try:
                    return str(random.randint(int(a), int(b)))
                except ValueError as e:
                    return f"参数无效: {e}"

            # 处理骰子表示法，如"3d6"、"3d6+2"、"2d20-1"等
            case [arg] if "d" in arg.lower():
                try:
                    return self._process_dice(arg)
                except ValueError as e:
                    return f"骰子格式无效: {e}"

            # 处理单个参数的情况，直接返回该参数
            case [arg]:
                return arg

            # 处理其他情况，从多个选项中随机选择一个
            case _:
                try:
                    clean_args = [a.strip() for a in args]
                    return random.choice(clean_args)
                except Exception as e:
                    return f"参数无效: {e}"

    def _is_num(self, s: str) -> bool:
        """检查字符串是否可以转换为整数（包括负数）

        Args:
            s: 要检查的字符串

        Returns:
            如果字符串可以转换为整数则返回True，否则返回False
        """
        return s.lstrip("-+").isdigit()

    def _process_dice(self, notation: str) -> str:
        """处理骰子表示法

        根据不同的骰子表示法调用相应的处理方法

        Args:
            notation: 骰子表示法字符串，如 "3d6", "2d20adv"

        Returns:
            骰子投掷结果的字符串表示

        Raises:
            ValueError: 当骰子表示法格式无效时抛出
        """
        # 处理优势骰和劣势骰
        adv_match = ADV_PATTERN.match(notation.lower())
        dis_match = DIS_PATTERN.match(notation.lower())

        if adv_match:
            return self._process_advantage(adv_match, True)
        elif dis_match:
            return self._process_advantage(dis_match, False)

        # 处理组合骰子表示法，如 2d6+1d4+3
        if "+" in notation or ("-" in notation and not notation.startswith("-")):
            return self._process_combine(notation)

        # 处理带上界的骰子，如 3d6u4 (结果最高为4)
        if "u" in notation.lower():
            return self._process_bound(notation, "u")
        # 处理带下界的骰子，如 3d6b2 (结果最低为2)
        if "b" in notation.lower():
            return self._process_bound(notation, "b")
        # 处理重投累加的骰子，如 3d6r5 (5或以上时重投并累加)
        if "r" in notation.lower():
            return self._process_reroll(notation, "r")
        # 处理重投的骰子，如 3d6t2 (2或以下时重投)
        if "t" in notation.lower():
            return self._process_reroll(notation, "t")
        # 处理保留高位或低位的骰子，如 4d6k3 (保留高3个), 4d6l2 (保留低2个)
        if "k" in notation.lower() or "l" in notation.lower():
            return self._process_keep(notation)

        # 处理标准骰子表示法，如 3d6
        parts = notation.lower().split("d")
        if len(parts) != 2:
            raise ValueError("骰子表示法必须包含一个'd'")

        # 如果没有指定骰子数量，默认为1
        num = 1 if parts[0] == "" else int(parts[0])
        if not self._is_num(parts[0]) and parts[0] != "":
            raise ValueError("骰子数量必须是整数")
        if not self._is_num(parts[1]):
            raise ValueError("骰子面数必须是整数")
        faces = int(parts[1])

        if num <= 0 or faces <= 0:
            raise ValueError("骰子数量和面数必须为正数")

        # 生成随机骰子结果
        rolls = [random.randint(1, faces) for _ in range(num)]
        result = sum(rolls)

        logger.debug(f"骰子投掷: {' + '.join(map(str, rolls))} = {result}")

        return str(result)

    def _process_advantage(self, match, is_advantage):
        """处理优势或劣势掷骰

        优势掷骰：投两次取较高值
        劣势掷骰：投两次取较低值

        Args:
            match: 正则表达式匹配结果
            is_advantage: 是否为优势掷骰，True为优势，False为劣势

        Returns:
            掷骰结果的字符串表示

        Raises:
            ValueError: 当参数无效时抛出
        """
        num_str, faces_str = match.groups()
        num = int(num_str) if num_str else 1
        faces = int(faces_str)

        if num <= 0 or faces <= 0:
            raise ValueError("骰子数量和面数都必须为正数")

        result = 0
        details = []

        for _ in range(num):
            roll1 = random.randint(1, faces)
            roll2 = random.randint(1, faces)
            chosen = max(roll1, roll2) if is_advantage else min(roll1, roll2)
            details.append(f"{chosen} [{roll1},{roll2}]")
            result += chosen

        logger.debug(
            f"{'优势' if is_advantage else '劣势'}掷骰: {' + '.join(details)} = {result}"
        )

        return str(result)

    def _process_bound(self, notation, bound_type):
        """处理带上界或下界的骰子

        上界(u)：如果骰子结果大于上界值，则使用上界值
        下界(b)：如果骰子结果小于下界值，则使用下界值

        Args:
            notation: 骰子表示法字符串，如 "3d6u4", "2d8b3"
            bound_type: 界限类型，"u"表示上界，"b"表示下界

        Returns:
            掷骰结果的字符串表示

        Raises:
            ValueError: 当骰子表示法格式无效时抛出
        """
        parts = notation.lower().split(bound_type)
        if len(parts) != 2:
            raise ValueError(f"无效的{'上' if bound_type == 'u' else '下'}界表示法")

        dice_part = parts[0]
        if not self._is_num(parts[1]):
            raise ValueError("界限值必须是整数")
        bound = int(parts[1])

        dice_parts = dice_part.split("d")
        if len(dice_parts) != 2:
            raise ValueError("骰子表示法必须包含一个'd'")

        num = 1 if dice_parts[0] == "" else int(dice_parts[0])
        if not self._is_num(dice_parts[0]) and dice_parts[0] != "":
            raise ValueError("骰子数量必须是整数")
        if not self._is_num(dice_parts[1]):
            raise ValueError("骰子面数必须是整数")
        faces = int(dice_parts[1])

        if num <= 0 or faces <= 0:
            raise ValueError("骰子数量和面数都必须为正数")

        rolls = []
        bounded_rolls = []

        for _ in range(num):
            roll = random.randint(1, faces)
            rolls.append(roll)
            if bound_type == "u" and roll > bound:
                bounded_rolls.append(f"{bound}({roll})")
                roll = bound
            elif bound_type == "b" and roll < bound:
                bounded_rolls.append(f"{bound}({roll})")
                roll = bound
            else:
                bounded_rolls.append(str(roll))

        result = (
            sum(min(r, bound) for r in rolls)
            if bound_type == "u"
            else sum(max(r, bound) for r in rolls)
        )

        logger.debug(
            f"{'上' if bound_type == 'u' else '下'}界掷骰: {' + '.join(bounded_rolls)} = {result}"
        )

        return str(result)

    def _process_reroll(self, notation, reroll_type):
        """处理重投或重投累加的骰子

        重投累加(r)：如果骰子结果大于等于阈值，则重投并将结果累加
        重投(t)：如果骰子结果小于等于阈值，则重投一次

        Args:
            notation: 骰子表示法字符串，如 "3d6r5", "2d8t2"
            reroll_type: 重投类型，"r"表示重投累加，"t"表示重投

        Returns:
            掷骰结果的字符串表示

        Raises:
            ValueError: 当骰子表示法格式无效时抛出
        """
        parts = notation.lower().split(reroll_type)
        if len(parts) != 2:
            raise ValueError(
                f"无效的{'重投累加' if reroll_type == 'r' else '重投'}表示法"
            )

        dice_part = parts[0]
        if not self._is_num(parts[1]):
            raise ValueError("重投条件值必须是整数")
        threshold = int(parts[1])

        dice_parts = dice_part.split("d")
        if len(dice_parts) != 2:
            raise ValueError("骰子表示法必须包含一个'd'")

        num = 1 if dice_parts[0] == "" else int(dice_parts[0])
        if not self._is_num(dice_parts[0]) and dice_parts[0] != "":
            raise ValueError("骰子数量必须是整数")
        if not self._is_num(dice_parts[1]):
            raise ValueError("骰子面数必须是整数")
        faces = int(dice_parts[1])

        if num <= 0 or faces <= 0:
            raise ValueError("骰子数量和面数都必须为正数")
        if threshold < 1 or threshold > faces:
            raise ValueError(f"重投阈值必须在1到{faces}之间")

        result = 0
        details = []

        for _ in range(num):
            roll_details = []
            roll = random.randint(1, faces)
            roll_details.append(str(roll))

            if reroll_type == "r":
                # 重投累加：当骰子结果大于等于阈值时，重投并累加结果
                current_sum = roll
                while roll >= threshold:
                    roll = random.randint(1, faces)
                    roll_details.append(f"+{roll}")
                    current_sum += roll
                result += current_sum
                details.append(
                    f"{current_sum} ({''.join(roll_details)})"
                    if len(roll_details) > 1
                    else str(current_sum)
                )
            else:
                # 重投：当骰子结果小于等于阈值时，重投一次
                if roll <= threshold:
                    reroll = random.randint(1, faces)
                    result += reroll
                    details.append(f"{reroll} ({roll}→{reroll})")
                else:
                    result += roll
                    details.append(str(roll))

        logger.debug(
            f"{'重投累加' if reroll_type == 'r' else '重投'}掷骰: {' + '.join(details)} = {result}"
        )

        return str(result)

    def _process_combine(self, notation: str) -> str:
        """处理组合骰子表示法，如 2d6+1d4+3

        可以组合多种骰子和固定值，如 2d6+1d4+3, 3d8-1d6+2

        Args:
            notation: 组合骰子表示法字符串

        Returns:
            组合掷骰结果的字符串表示
        """
        matches = re.findall(DICE_PATTERN, notation)
        total = 0
        details = []

        for match in matches:
            expr = match[0] if match[0] else match[1]
            if not expr:
                continue

            # 处理固定值修正
            if "d" not in expr:
                modifier = int(expr)
                total += modifier
                details.append(f"+{modifier}" if modifier > 0 else str(modifier))
                continue

            # 处理带符号的骰子表达式
            sign = 1
            if expr.startswith("-"):
                sign = -1
                expr = expr[1:]
            elif expr.startswith("+"):
                expr = expr[1:]

            result_str = self._process_dice(expr)
            result_value = int(result_str)
            result_value *= sign
            total += result_value
            details.append(
                f"-[{result_str}]"
                if sign == -1
                else f"+[{result_str}]"
                if details
                else f"[{result_str}]"
            )

        logger.debug(f"组合掷骰: {' '.join(details)} = {total}")

        return str(total)

    def _process_keep(self, notation: str) -> str:
        """处理保留高/低位的骰子表示法

        保留高位(k)：如 4d6k3 表示投4个骰子保留高3个
        保留低位(l)：如 4d6l2 表示投4个骰子保留低2个

        Args:
            notation: 骰子表示法字符串，如 "4d6k3", "4d6l2"

        Returns:
            掷骰结果的字符串表示

        Raises:
            ValueError: 当骰子表示法格式无效时抛出
        """
        if "k" in notation.lower():
            parts = notation.lower().split("k")
            keep_highest = True
        elif "l" in notation.lower():
            parts = notation.lower().split("l")
            keep_highest = False
        else:
            raise ValueError("无效的保留表示法")

        dice_part = parts[0]
        dice_parts = dice_part.split("d")
        if len(dice_parts) != 2:
            raise ValueError("骰子表示法必须包含一个'd'")

        num = 1 if dice_parts[0] == "" else int(dice_parts[0])
        if not self._is_num(dice_parts[0]) and dice_parts[0] != "":
            raise ValueError("骰子数量必须是整数")
        if not self._is_num(dice_parts[1]):
            raise ValueError("骰子面数必须是整数")
        faces = int(dice_parts[1])

        if not self._is_num(parts[1]):
            raise ValueError("保留数量必须是整数")
        keep = int(parts[1])

        if num <= 0 or faces <= 0 or keep <= 0:
            raise ValueError("骰子数量、面数和保留数量都必须为正数")
        if keep > num:
            raise ValueError("保留数量不能大于骰子数量")

        # 生成随机骰子结果并排序
        rolls = [random.randint(1, faces) for _ in range(num)]
        sorted_rolls = sorted(rolls, reverse=keep_highest)
        kept_rolls = sorted_rolls[:keep]
        dropped_rolls = sorted_rolls[keep:]
        result = sum(kept_rolls)

        kept_str = "+".join(map(str, kept_rolls))
        if dropped_rolls:
            dropped_str = "+".join(map(str, dropped_rolls))
            logger.debug(
                f"{'保留高位' if keep_highest else '保留低位'}掷骰: {kept_str} [丢弃: {dropped_str}] = {result}"
            )
        else:
            logger.debug(
                f"{'保留高位' if keep_highest else '保留低位'}掷骰: {kept_str} = {result}"
            )

        return str(result)
