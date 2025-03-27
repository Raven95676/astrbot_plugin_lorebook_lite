import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Trigger:
    """定义触发器"""

    name: str = field(default_factory=lambda: f"authors_note_{uuid.uuid4().hex}")
    type: str = "keywords"
    content: str = ""
    match: str | None = None
    conditional: str | None = None
    recursive_scan: bool = False
    recursion_depth: int = 0
    priority: int = 0
    block: bool = False
    use_logic: bool = True
    position: str = "sys_start"
    probability: float = 1.0
    actions: list[str] = field(default_factory=list)
    _last_triggered: int = field(default_factory=lambda: int(datetime.now().timestamp()), repr=False)

    def __post_init__(self):
        self.probability = max(0, min(self.probability, 1))

        if self.position not in ["sys_start", "user_start", "sys_end", "user_end"]:
            self.position = "sys_start"

        if self.type not in ["regex", "keywords", "listener"]:
            self.type = "keywords"

    @property
    def last_triggered(self):
        """返回上次触发的时间戳并更新"""
        self._last_triggered = int(datetime.now().timestamp())
        return self._last_triggered

    @last_triggered.setter
    def last_triggered(self, value):
        """设置上次触发的时间戳"""
        self._last_triggered = value


@dataclass
class Permission:
    """定义权限"""

    name: str
    triggers: list[str] = field(default_factory=list)


@dataclass
class Result:
    """定义触发结果"""

    sys_start: list[str] = field(default_factory=list)
    user_start: list[str] = field(default_factory=list)
    sys_end: list[str] = field(default_factory=list)
    user_end: list[str] = field(default_factory=list)
    res_start: list[str] = field(default_factory=list)
    res_end: list[str] = field(default_factory=list)
