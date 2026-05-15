"""Gateway runtime façade over support, capability, app, adapter, and factory modules."""

from __future__ import annotations

from .runtime_support import (
    CHAT_BOT_ADAPTER_ID,
    DEFAULT_GATEWAY_ACCOUNT_ID,
    DINGDING_ADAPTER_ID,
    DISCORD_ADAPTER_ID,
    FEISHU_ADAPTER_ID,
    TELEGRAM_ADAPTER_ID,
    WECOM_ADAPTER_ID,
    WEIXIN_ADAPTER_ID,
    WEBHOOK_ADAPTER_ID,
)
from .runtime_app import (
    GatewayApp,
)
from .runtime_adapters import (
    ChatBotMessagingAdapter,
    DingdingMessagingAdapter,
    DiscordMessagingAdapter,
    FeishuMessagingAdapter,
    TelegramMessagingAdapter,
    WecomMessagingAdapter,
    WeixinMessagingAdapter,
    WebhookMessagingAdapter,
)
from .runtime_factory import (
    build_gateway_app,
    register_builtin_gateway_adapters,
)


__all__ = [
    "CHAT_BOT_ADAPTER_ID",
    "DEFAULT_GATEWAY_ACCOUNT_ID",
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
    "GatewayApp",
    "TelegramMessagingAdapter",
    "WecomMessagingAdapter",
    "WeixinMessagingAdapter",
    "WebhookMessagingAdapter",
    "build_gateway_app",
    "register_builtin_gateway_adapters",
]
