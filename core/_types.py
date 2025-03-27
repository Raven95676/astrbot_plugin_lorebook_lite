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
    priority: int = 0
    block: bool = False
    use_logic: bool = True
    position: str = "sys_start"
    probability: float = 1.0
    actions: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.probability = max(0, min(self.probability, 1))

        if self.position not in ["sys_start", "user_start", "sys_end", "user_end"]:
            self.position = "sys_start"

        if self.type not in ["regex", "keywords", "listener"]:
            self.type = "keywords"


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
