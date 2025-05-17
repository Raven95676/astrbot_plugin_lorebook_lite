from datetime import datetime
from typing import Any
from typing import TYPE_CHECKING

from dateutil import relativedelta

if TYPE_CHECKING:
    from ..parser import LoreParser

# 定义不同时间格式的格式化字符串
TIME_FORMATS = {
    "date": "%Y-%m-%d",  # 日期格式
    "time": "%H:%M",  # 时间格式
    "year": "%Y",  # 年份格式
    "month": "%m",  # 月份格式
    "day": "%d",  # 日期格式
    "hour": "%H",  # 小时格式
    "minute": "%M",  # 分钟格式
}


class TimeHandler:
    """时间处理器类，用于管理和操作时间相关功能"""

    def __init__(self, parser: "LoreParser"):
        """初始化时间处理器

        Args:
            parser: 解析器实例，用于访问和修改当前时间
        """
        self.parser: "LoreParser" = parser

    def handle_time_oper(self, args: list[str]) -> str:
        """处理时间相关操作

        Args:
            args: 操作参数列表

        Returns:
            操作结果字符串，通常为格式化后的时间
        """
        # 如果没有参数，返回当前时间
        if not args:
            return self.parser._current_time.strftime("%Y-%m-%d %H:%M")

        arg = args[0]
        match arg:
            # 返回计算后的真实世界空闲时间
            case "real_idle":
                return self._get_idle_duration(self.parser._real_idle)
            # 返回计算后的虚拟世界空闲时间
            case "world_idle":
                return self._get_idle_duration(self.parser._world_idle)
            # 如果参数是预定义的时间格式，返回相应格式的时间
            case format_key if format_key in TIME_FORMATS:
                return self.parser._current_time.strftime(TIME_FORMATS[format_key])
            # 如果参数以+或-开头，表示时间调整
            case delta if delta.startswith("+") or delta.startswith("-"):
                positive = delta.startswith("+")
                delta_value = delta[1:]
                return self._adjust_time(delta_value, positive=positive)
            # 否则尝试将参数解析为完整时间字符串
            case time_str:
                try:
                    new_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    return self._set_time(new_time)
                except ValueError:
                    # 如果解析失败，返回当前时间
                    return self.parser._current_time.strftime("%Y-%m-%d %H:%M")

    def _set_time(self, new_time: datetime | str) -> str:
        """设置绝对时间

        Args:
            new_time: 新的时间值，可以是datetime对象或时间字符串

        Returns:
            设置后的时间字符串
        """
        match new_time:
            # 如果是datetime对象，直接设置
            case datetime() as dt:
                self.parser._current_time = dt
                return self.parser._current_time.strftime("%Y-%m-%d %H:%M")
            # 如果是字符串，尝试解析为datetime
            case str() as time_str:
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    self.parser._current_time = dt
                    return self.parser._current_time.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    return "日期格式无效"
            case _:
                return "时间输入类型无效"

    def _adjust_time(self, delta_input: Any, positive: bool = True) -> str:
        """处理时间调整

        Args:
            delta_input: 时间增量，可以是relativedelta对象或字符串
            positive: 是否为正向调整，True表示增加时间，False表示减少时间

        Returns:
            调整后的时间字符串
        """
        match delta_input:
            # 如果是relativedelta对象，直接应用
            case relativedelta.relativedelta() as delta:
                if not positive:
                    # 如果是负向调整，反转所有时间单位
                    delta = relativedelta.relativedelta(
                        years=-delta.years,
                        months=-delta.months,
                        days=-delta.days,
                        hours=-delta.hours,
                        minutes=-delta.minutes,
                        seconds=-delta.seconds,
                    )
                self.parser._current_time += delta
                return self.parser._current_time.strftime("%Y-%m-%d %H:%M")
            # 如果是字符串，解析为时间增量
            case str() as delta_str:
                try:
                    # 解析格式：数字+单位，如"1Y"表示1年，"30m"表示30分钟
                    amount, unit = delta_str[:-1], delta_str[-1]
                    amount_i: int = int(amount) * (1 if positive else -1)
                    # 根据单位创建相应的relativedelta对象
                    match unit:
                        case "Y":  # 年
                            delta = relativedelta.relativedelta(years=amount_i)
                        case "M":  # 月
                            delta = relativedelta.relativedelta(months=amount_i)
                        case "D":  # 日
                            delta = relativedelta.relativedelta(days=amount_i)
                        case "h":  # 小时
                            delta = relativedelta.relativedelta(hours=amount_i)
                        case "m":  # 分钟
                            delta = relativedelta.relativedelta(minutes=amount_i)
                        case _:
                            return "无效的时间单位"
                    # 应用时间增量
                    self.parser._current_time += delta
                    self.parser._world_idle["before"] = self.parser._world_idle["after"]
                    self.parser._world_idle["after"] = self.parser._current_time
                    return self.parser._current_time.strftime("%Y-%m-%d %H:%M")
                except (ValueError, IndexError):
                    return "无效的时间增量格式"
            case _:
                return "时间增量输入类型无效"

    def _get_idle_duration(self, times: dict[str, datetime]) -> str:
        """计算并返回人性化的空闲时间字符串

        Args:
            times: 包含 "before" 和 "after" 时间戳的字典

        Returns:
            人性化的空闲时间描述，如 "5分钟前"、"2小时前"、"3天前" 等
            或未来时间描述，如 "5分钟后"、"2小时后"、"3天后" 等
        """
        # 计算时间差（秒）
        idle_seconds = (times["before"] - times["after"]).total_seconds()

        # 确定是过去还是未来
        is_past = idle_seconds > 0
        suffix = "前" if is_past else "后"

        idle_seconds = abs(idle_seconds)

        if is_past:
            delta = relativedelta.relativedelta(times["before"], times["after"])
        else:
            delta = relativedelta.relativedelta(times["after"], times["before"])

        if idle_seconds < 60:
            return "刚刚"
        elif idle_seconds < 3600:  # 1小时内
            minutes = delta.minutes
            return f"{minutes}分钟{suffix}"
        elif idle_seconds < 86400:  # 24小时内
            hours = delta.hours
            return f"{hours}小时{suffix}"
        elif idle_seconds < 2592000:  # 约30天内
            days = delta.days
            return f"{days}天{suffix}"
        elif idle_seconds < 31536000:  # 1年内
            months = delta.months + delta.years * 12
            return f"{months}个月{suffix}"
        else:
            years = delta.years
            return f"{years}年{suffix}"
