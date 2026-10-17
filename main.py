# -*- coding: utf-8 -*-
"""群消息说话人标注插件（astrbot_plugin_sender_tag）v1.1.0

解决群聊多成员共用同一会话历史时，LLM 无法区分每条 user 消息来自谁的问题：
AstrBot 主链路把 event.message_str 原样作为 prompt（req.prompt = event.message_str），
持久会话历史里的用户消息不带说话人信息，多人交替发言时上下文接续混乱。

本插件在 LLM 请求前给群聊消息加上「昵称(QQ号): 」前缀，随会话历史持久化，
让 LLM 在后续轮次中也能分辨历史里每条消息的说话人。私聊默认不加。

注入格式默认与常见的「昵称(QQ号): 内容」上下文写法保持一致，可用配置调整。
"""

from __future__ import annotations

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star

VERSION = "1.1.0"

# extra 标记：携带该标记的请求其 prompt 已自带说话人信息（如主动回复插件的模板文本），
# 跳过加前缀，避免出现「张三(123): 群里张三(123)发了一条消息」的叠加
SKIP_EXTRA_KEY = "sender_tag_skip"


class Main(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None) -> None:
        super().__init__(context)
        cfg = config if isinstance(config, dict) and len(config) > 0 else {}

        self.enabled = bool(cfg.get("enabled", True))
        self.include_qq = bool(cfg.get("include_qq", True))
        self.tag_private_chat = bool(cfg.get("tag_private_chat", False))
        self.separator = str(cfg.get("separator") or ": ")
        try:
            n = int(cfg.get("max_name_len", 0))
        except (TypeError, ValueError):
            n = 0
        self.max_name_len = max(0, n)  # 0 = 不截断

        logger.info(
            f"[sender_tag] v{VERSION} 已加载："
            f"{'启用' if self.enabled else '停用'}｜"
            f"QQ号={'含' if self.include_qq else '不含'}｜"
            f"私聊={'标注' if self.tag_private_chat else '不标注'}｜"
            f"昵称截断={self.max_name_len or '不截断'}"
        )

    def _build_prefix(self, event: AstrMessageEvent) -> str:
        """拼出「昵称(QQ号): 」前缀；缺少必要信息时返回空串表示不标注。"""
        sender_name = (event.get_sender_name() or "").strip()
        sender_id = str(event.get_sender_id() or "").strip()
        if self.max_name_len > 0 and len(sender_name) > self.max_name_len:
            sender_name = sender_name[: self.max_name_len]
        if self.include_qq:
            if not sender_id:
                return ""
            sender = f"{sender_name}({sender_id})" if sender_name else sender_id
        else:
            sender = sender_name or sender_id
        if not sender:
            return ""
        return f"{sender}{self.separator}"

    @filter.on_llm_request()
    async def tag_sender(self, event: AstrMessageEvent, req: ProviderRequest):
        """群聊 LLM 请求：给 prompt 加说话人前缀（随会话历史持久化）。"""
        try:
            if not self.enabled:
                return
            if event.get_extra(SKIP_EXTRA_KEY):
                return  # 上游已自带说话人信息

            group_id = event.get_group_id()
            if not group_id and not self.tag_private_chat:
                return  # 私聊默认不需要标注

            prompt = req.prompt or ""
            if not prompt.strip():
                return  # 纯图片/纯音频消息，prompt 为空不动

            prefix = self._build_prefix(event)
            if not prefix:
                return
            if prompt.startswith(prefix):
                return  # 幂等：避免重复标注（插件重载/多插件叠加）

            req.prompt = f"{prefix}{prompt}"
            logger.debug(
                f"[sender_tag] 已加说话人前缀：{prefix!r}｜群={group_id or '私聊'}｜"
                f"prompt 原长 {len(prompt)}"
            )
        except Exception as e:
            # 标注失败不影响主流程，prompt 保持原样
            logger.error(f"[sender_tag] 加前缀失败（已跳过）: {e}", exc_info=True)
