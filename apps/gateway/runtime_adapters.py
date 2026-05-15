"""Gateway messaging adapter façade.

The concrete platform adapters now live under `apps/gateway/platforms/` so each
IM surface can evolve independently while older imports remain stable.
"""

from __future__ import annotations

from .platforms import (
    ChatBotMessagingAdapter,
    DingdingMessagingAdapter,
    DiscordMessagingAdapter,
    FeishuMessagingAdapter,
    TelegramMessagingAdapter,
    WecomMessagingAdapter,
    WeixinMessagingAdapter,
    WebhookMessagingAdapter,
)
from .runtime_support import (
    CHAT_BOT_ADAPTER_ID,
    DINGDING_ADAPTER_ID,
    DISCORD_ADAPTER_ID,
    FEISHU_ADAPTER_ID,
    TELEGRAM_ADAPTER_ID,
    WECOM_ADAPTER_ID,
    WEIXIN_ADAPTER_ID,
    WEBHOOK_ADAPTER_ID,
)

__all__ = [
    "CHAT_BOT_ADAPTER_ID",
    "DINGDING_ADAPTER_ID",
    "DISCORD_ADAPTER_ID",
    "FEISHU_ADAPTER_ID",
    "TELEGRAM_ADAPTER_ID",
    "WECOM_ADAPTER_ID",
    "WEIXIN_ADAPTER_ID",
    "WEBHOOK_ADAPTER_ID",
    "ChatBotMessagingAdapter",
    "DingdingMessagingAdapter",
    "DiscordMessagingAdapter",
    "FeishuMessagingAdapter",
    "TelegramMessagingAdapter",
    "WecomMessagingAdapter",
    "WeixinMessagingAdapter",
    "WebhookMessagingAdapter",
]
