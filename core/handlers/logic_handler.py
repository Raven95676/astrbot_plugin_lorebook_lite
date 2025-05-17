from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import LoreParser

# 定义支持的比较运算符及其对应的函数
OPERATORS = [
    ("==", lambda x, y: x == y),  # 等于
    ("!=", lambda x, y: x != y),  # 不等于
    ("<", lambda x, y: x < y),  # 小于
    (">", lambda x, y: x > y),  # 大于
    ("<=", lambda x, y: x <= y),  # 小于等于
    (">=", lambda x, y: x >= y),  # 大于等于
]


class LogicHandler:
    """逻辑处理器类，用于处理条件判断和逻辑运算"""

    def __init__(self, parser: "LoreParser"):
        """初始化逻辑处理器

        Args:
            parser: 解析器实例，用于解析占位符
        """
        self.parser: "LoreParser" = parser

    def handle_logic_oper(self, function: str, args: list[str]) -> str:
        """处理逻辑操作

        Args:
            function: 逻辑函数名称，如'if'、'and'、'or'
            args: 函数参数列表

        Returns:
            逻辑操作的结果字符串
        """
        if not args:
            return "参数错误"

        # 处理所有参数中的占位符
        processed_args = [self.parser.parse_placeholder(arg) for arg in args]

        match function:
            case "if":  # 条件判断
                if len(processed_args) < 2:
                    return "条件参数不足"

                condition_result = self._eval_cond(processed_args[0])
                # 如果条件为真，返回第二个参数，否则返回第三个参数（如果存在）
                result = (
                    processed_args[1]
                    if condition_result
                    else (processed_args[2] if len(processed_args) > 2 else "")
                )
                return result

            case "and":  # 逻辑与
                # 所有条件都为真时返回"true"，否则返回"false"
                return (
                    "true"
                    if all(self._eval_cond(cond) for cond in processed_args)
                    else "false"
                )

            case "or":  # 逻辑或
                # 任一条件为真时返回"true"，否则返回"false"
                return (
                    "true"
                    if any(self._eval_cond(cond) for cond in processed_args)
                    else "false"
                )

            case "not":  # 逻辑非
                # 任一条件为真时返回"false"，否则返回"true"
                if len(processed_args) != 1:
                    return "逻辑非操作需要一个参数"
                return "true" if not self._eval_cond(processed_args[0]) else "false"

            case _:
                return "未知逻辑操作"

    def _eval_cond(self, condition: str) -> bool:
        """处理条件表达式

        Args:
            condition: 条件表达式字符串

        Returns:
            条件表达式的布尔结果
        """
        if not isinstance(condition, str):
            condition = str(condition)

        condition = condition.strip()
        if not condition:
            return False

        # 处理布尔字面值
        if condition.lower() == "true" or condition == "1":
            return True
        if condition.lower() == "false" or condition == "0" or condition == "":
            return False

        # 处理非逻辑（!）
        if condition.startswith("!"):
            return not self._eval_cond(condition[1:].strip())

        # 处理逻辑与（&&）
        if "&&" in condition:
            parts = condition.split("&&")
            return all(self._eval_cond(part.strip()) for part in parts if part.strip())

        # 处理逻辑或（||）
        if "||" in condition:
            parts = condition.split("||")
            return any(self._eval_cond(part.strip()) for part in parts if part.strip())

        # 处理比较运算符
        for op, func in OPERATORS:
            if op in condition:
                try:
                    # 分割左右操作数，仅按第一次出现的操作符分割
                    left, right = condition.split(op, 1)
                    left, right = left.strip(), right.strip()

                    # 尝试数值转换
                    left_val = self._try_numeric_conversion(left)
                    right_val = self._try_numeric_conversion(right)

                    # 应用比较函数
                    return func(left_val, right_val)
                except Exception:
                    # 任何异常情况下返回False
                    return False

        # 如果没有匹配到任何运算符，将非空条件视为真
        return bool(condition)

    def _try_numeric_conversion(self, value: str) -> int | float | str:
        """尝试将值转换为数值类型

        Args:
            value: 要转换的字符串值

        Returns:
            转换后的值，可能是整数、浮点数或原始字符串
        """
        try:
            # 尝试整数转换
            if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                return int(value)

            # 尝试浮点数转换
            float_val = float(value)
            # 如果是整数值的浮点数，转换为整数
            return int(float_val) if float_val.is_integer() else float_val
        except (ValueError, AttributeError):
            # 转换失败则返回原始字符串
            return value
