import os
import shutil
from collections import deque

import yaml  # type: ignore

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.provider.entites import LLMResponse, ProviderRequest
from astrbot.core.star.filter.event_message_type import EventMessageType

from .core._types import LoreResult  # type: ignore
from .core.parser import LoreParser  # type: ignore


@register("astrbot_plugin_lorebook_lite", "Raven95676", "lorebook插件", "0.1.0")
class LorePlugin(Star):
    """Lorebook插件，用于根据预设规则处理聊天内容并修改LLM请求"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        # 存储每个会话的Lore解析器
        self.lore_sessions: dict[str, LoreParser] = {}
        # 存储每个会话的Lore处理结果
        self.res_map: dict[str, deque[LoreResult]] = {}
        # 备份原始人格配置
        self.persona_bak = {}
        for persona in self.context.provider_manager.personas:
            self.persona_bak[persona["name"]] = {"prompt": persona["prompt"]}

    async def initialize(self):
        """初始化lorebook配置"""
        self.scan_depth = self.config.get("scan_depth", 1)
        # 确保扫描深度至少为1
        if self.scan_depth < 1:
            self.scan_depth = 1
        # 如果配置中包含AI回复，则扫描深度翻倍（同时考虑用户和AI的消息）
        if self.config.get("include_ai", False):
            self.scan_depth = self.scan_depth * 2
        logger.info(f"lorebook | 扫描深度: {self.scan_depth}")

        # 创建lorebooks存储目录
        lorebook_path = os.path.join(os.getcwd(), "data", "lorebooks")
        os.makedirs(lorebook_path, exist_ok=True)

        # 获取示例lorebook文件的路径
        examples_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "examples"
        )
        # 如果示例目录存在，复制示例lorebook到用户目录
        if os.path.exists(examples_path):
            for file in os.listdir(examples_path):
                if file.endswith(".yaml"):
                    src_file = os.path.join(examples_path, file)
                    dst_file = os.path.join(lorebook_path, file)
                    # 只有在目标文件不存在时才复制，避免覆盖用户自定义的lorebook
                    if not os.path.exists(dst_file):
                        logger.info(f"复制示例lorebook: {file}")
                        shutil.copy(src_file, dst_file)

        try:
            # 尝试加载配置中指定的lorebook文件
            with open(
                os.path.join(
                    lorebook_path, f"{self.config.get('lorebook_name', '')}.yaml"
                ),
                "r",
                encoding="utf-8",
            ) as f:
                # 使用yaml解析器加载lorebook配置
                self.lorebook = yaml.safe_load(f)
                logger.info("lorebook | 已加载lorebook配置")
        except Exception as e:
            # 如果加载失败，记录错误并将lorebook设为None
            logger.error(f"无法加载lorebook配置: {e!s}")
            self.lorebook = None

    async def _get_curr_persona(self, umo: str):
        """获取当前会话使用的人格ID和人格对象"""
        curr_cid = await self.context.conversation_manager.get_curr_conversation_id(umo)
        conversation = await self.context.conversation_manager.get_conversation(
            umo, curr_cid
        )
        persona_id = conversation.persona_id if conversation else None

        # 如果persona_id为空且不是明确设置为"[%None]"，则使用默认人格
        if not persona_id and persona_id != "[%None]":
            if self.context.provider_manager.selected_default_persona:
                persona_id = self.context.provider_manager.selected_default_persona[
                    "name"
                ]

        persona = next(
            (
                p
                for p in self.context.provider_manager.personas
                if p["name"] == persona_id
            ),
            None,
        )

        return persona_id, persona

    @filter.event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """处理所有消息事件，计算Lore规则匹配结果"""
        if not self.lorebook:
            return

        umo = event.unified_msg_origin

        # 为每个会话创建一个独立的解析器
        if umo not in self.lore_sessions:
            self.lore_sessions[umo] = LoreParser(self.lorebook, self.scan_depth)

        # 设置解析器的发送者信息
        parser = self.lore_sessions[umo]
        parser.sender = event.get_sender_id()
        parser.sender_name = event.get_sender_name() or event.get_sender_id()

        # 处理消息文本
        msg = event.get_message_str()
        msg_clean = " ".join(msg.split())
        parser.messages.append(msg_clean)

        # 处理聊天内容，获取匹配结果
        res = parser.process_chat()

        # 初始化结果队列（如果不存在）
        if umo not in self.res_map:
            self.res_map[umo] = deque()
        self.res_map[umo].append(res)

        logger.debug(str(parser))

    @filter.on_llm_request(priority=1)
    async def on_llm_req(self, event: AstrMessageEvent, request: ProviderRequest):
        """在LLM请求前处理，插入Lore规则匹配结果"""
        umo = event.unified_msg_origin

        if umo not in self.res_map:
            return

        # 获取会话正在使用的人格
        _, persona = await self._get_curr_persona(umo)

        # 获取当前会话的所有处理结果
        results = list(self.res_map[umo])
        logger.debug(f"lorebook | {umo} | {results}")

        # 合并所有结果中的提示内容
        sys_start = "\n".join(
            [line for res in results if res.sys_start for line in res.sys_start]
        )
        user_start = "\n".join(
            [line for res in results if res.user_start for line in res.user_start]
        )
        sys_end = "\n".join(
            [line for res in results if res.sys_end for line in res.sys_end]
        )
        user_end = "\n".join(
            [line for res in results if res.user_end for line in res.user_end]
        )

        # 将处理结果插入到LLM请求中
        if sys_start and persona:
            persona["prompt"] = f"{sys_start}\n{persona['prompt']}"
        if user_start:
            request.prompt = f"{user_start}\n{request.prompt}"
        if sys_end and persona:
            persona["prompt"] = f"{persona['prompt']}\n{sys_end}"
        if user_end:
            request.prompt = f"{request.prompt}\n{user_end}"

    @filter.on_llm_response()
    async def on_llm_res(self, event: AstrMessageEvent, response: LLMResponse):
        """在LLM响应后处理"""
        umo = event.unified_msg_origin

        # 添加Bot回复到消息历史
        if umo in self.lore_sessions and self.config.get("include_ai", False):
            msg = response.completion_text
            msg_clean = " ".join(msg.split())
            self.lore_sessions[umo].messages.append(msg_clean)

        # 清除结果缓存并还原人格
        if umo in self.res_map:
            self.res_map[umo].clear()

            # 获取当前人格并还原
            persona_id, _ = await self._get_curr_persona(umo)
            if persona_id and persona_id in self.persona_bak:
                # 找到对应的persona对象并还原prompt
                for p in self.context.provider_manager.personas:
                    if p["name"] == persona_id:
                        p["prompt"] = self.persona_bak[persona_id]["prompt"]
                        break

            logger.debug(f"lorebook | {umo} | 清除lorebook缓存并还原人格 {persona_id}")
