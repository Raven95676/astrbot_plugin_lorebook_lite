import uuid
from dataclasses import dataclass, field


@dataclass(slots=True)
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
    max_trig: int = -1  # -1 表示无限制

    def __post_init__(self):
        self.probability = max(0, min(self.probability, 1))

        if self.position not in ["sys_start", "user_start", "sys_end", "user_end"]:
            self.position = "sys_start"

        if self.type not in ["regex", "keywords", "listener"]:
            self.type = "keywords"

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return (
            f"Trigger(name={self.name}, type={self.type}, content='{self.content if len(self.content) < 15 else self.content[:15]}', "
            f"match={self.match}, conditional={self.conditional}, priority={self.priority}, "
            f"block={self.block}, use_logic={self.use_logic}, position={self.position}, "
            f"probability={self.probability}, actions={self.actions}, max_trig={self.max_trig})"
        )


@dataclass(slots=True)
class LoreResult:
    """定义触发结果"""

    sys_start: list[str] = field(default_factory=list)
    user_start: list[str] = field(default_factory=list)
    sys_end: list[str] = field(default_factory=list)
    user_end: list[str] = field(default_factory=list)
    res_start: list[str] = field(default_factory=list)
    res_end: list[str] = field(default_factory=list)
