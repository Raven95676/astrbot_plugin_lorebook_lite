from functools import lru_cache
from typing import Any


class VarHandler:
    """变量处理器类，用于管理和操作不同作用域的变量"""

    def __init__(self, parser):
        """初始化变量处理器

        Args:
            parser: 解析器实例，用于解析占位符和存储变量数据
        """
        self.parser = parser

    @lru_cache(maxsize=64)
    def _get_scope_key(self, scope: str) -> str:
        """获取作用域键

        Args:
            scope: 变量作用域

        Returns:
            作用域键，全局作用域为"world"，用户作用域为"用户ID:作用域"
        """
        scope = self.parser.parse_placeholder(scope)
        scope_key = scope if scope == "world" else f"{self.parser.sender}:{scope}"

        # 如果作用域不存在，则创建并复制对应作用域的变量
        if scope_key not in self.parser._vars:
            self.parser._vars[scope_key] = self.parser._vars.get(scope, {}).copy()

        return scope_key

    @lru_cache(maxsize=128)
    def _parse_var_scope(self, var: str, default_scope: str) -> tuple[str, str]:
        """解析变量的作用域和名称

        Args:
            var: 变量标识符，格式可以是"scope.name"或"name"
            default_scope: 默认作用域

        Returns:
            (作用域, 变量名)元组
        """
        if "." in var:
            scope_name, var_name = var.split(".", 1)
            return scope_name, var_name
        return default_scope, var

    def handle_var_oper(
        self, function: str, args: list[str], scope: str = "world"
    ) -> str:
        """处理变量操作

        Args:
            function: 操作类型，可选值: set(设置), get(获取), del(删除), add(加), sub(减), mul(乘), div(除)
            args: 操作参数列表
            scope: 默认变量作用域，默认为"world"(全局)

        Returns:
            操作结果字符串
        """
        if not args:
            return "参数错误"

        match (function, len(args)):
            case ("set", n) if n >= 2:
                # 设置变量值
                target_scope, var_name = self._parse_var_scope(args[0], scope)
                value = args[1]
                return self._set_var(var_name, value, target_scope)

            case ("get", 1):
                # 获取变量值
                target_scope, var_name = self._parse_var_scope(args[0], scope)
                return str(self._get_var(var_name, target_scope))

            case ("del", 1):
                # 删除变量
                target_scope, var_name = self._parse_var_scope(args[0], scope)
                self._del_var(var_name, target_scope)
                return ""

            case ("add" | "sub" | "mul" | "div", 2):
                # 数学运算
                x_scope, x_var = self._parse_var_scope(args[0], scope)
                y_scope, y_var = self._parse_var_scope(args[1], scope)

                x = self._get_num(x_var, x_scope)
                y = self._get_num(y_var, y_scope)

                # 如果不是数字，则进行字符串拼接
                if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                    return f"{str(x)}{str(y)}"

                # 执行相应的数学运算
                match function:
                    case "add":
                        result = x + y
                    case "sub":
                        result = x - y
                    case "mul":
                        result = x * y
                    case "div":
                        if y == 0:
                            return "除以零错误"
                        result = x / y

                return str(result)

            case _:
                return "参数错误"

    def _get_var(self, var_name: str, scope: str = "world") -> Any:
        """获取变量值

        Args:
            var_name: 变量名
            scope: 变量作用域，默认为"world"(全局)

        Returns:
            变量值，如果变量不存在则返回空字符串
        """
        var_name = self.parser.parse_placeholder(var_name)
        scope_key = self._get_scope_key(scope)
        return self.parser.parse_placeholder(
            self.parser._vars[scope_key].get(var_name, "")
        )

    def _set_var(self, var_name: str, value: Any, scope: str = "world") -> str:
        """设置变量值

        Args:
            var_name: 变量名
            value: 变量值
            scope: 变量作用域，默认为"world"(全局)

        Returns:
            设置的变量值
        """
        var_name = self.parser.parse_placeholder(var_name)
        value = self.parser.parse_placeholder(str(value))
        scope_key = self._get_scope_key(scope)
        self.parser._vars[scope_key][var_name] = value
        return value

    def _del_var(self, var_name: str, scope: str = "world") -> None:
        """删除变量

        Args:
            var_name: 变量名
            scope: 变量作用域，默认为"world"(全局)
        """
        var_name = self.parser.parse_placeholder(var_name)
        scope_key = self._get_scope_key(scope)
        self.parser._vars[scope_key].pop(var_name, None)

    @lru_cache(maxsize=256)
    def _get_num(self, arg: str, scope: str = "world") -> int | float | str:
        """获取数字值

        尝试将参数转换为数字，如果失败则尝试获取同名变量的值并转换

        Args:
            arg: 数字字面量或变量名
            scope: 变量作用域，默认为"world"(全局)

        Returns:
            数字值或原始字符串
        """
        try:
            # 尝试转换为整数或浮点数
            num = float(arg)
            return int(num) if num.is_integer() else num
        except (ValueError, TypeError):
            val = self._get_var(arg, scope)
            try:
                num = float(val)
                return int(num) if num.is_integer() else num
            except (ValueError, TypeError):
                return val if val != "" else arg
