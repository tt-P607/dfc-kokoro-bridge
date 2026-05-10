"""DFC Kokoro Bridge Prompt 状态注入处理器。

监听 on_prompt_build 事件，在 default_chatter 构建 user prompt 时把插件维护的
私聊运行状态追加到 values["extra"]。
"""

from __future__ import annotations

from typing import Any

from src.app.plugin_system.api.event_api import EventDecision
from src.app.plugin_system.api.log_api import get_logger
from src.app.plugin_system.api.stream_api import get_stream_info
from src.app.plugin_system.base import BaseEventHandler

from ..config import DFCKokoroBridgeConfig
from ..services.state_service import DFCKokoroStateService

logger = get_logger("dfc_kokoro_bridge.prompt")


class DFCKokoroPromptStateInjector(BaseEventHandler):
    """向 DFC user prompt extra 注入私聊运行状态。"""

    handler_name: str = "dfc_kokoro_prompt_state_injector"
    handler_description: str = "在 default_chatter user prompt 中注入 DFC Kokoro Bridge 运行状态"
    weight: int = 12
    intercept_message: bool = False
    init_subscribe: list[str] = ["on_prompt_build"]

    def _get_config(self) -> DFCKokoroBridgeConfig:
        """获取插件配置。"""
        config = self.plugin.config
        if isinstance(config, DFCKokoroBridgeConfig):
            return config
        return DFCKokoroBridgeConfig()

    async def execute(
        self,
        event_name: str,
        params: dict[str, Any],
    ) -> tuple[EventDecision, dict[str, Any]]:
        """处理 prompt 构建事件。

        Args:
            event_name: 事件名称。
            params: on_prompt_build 事件参数。

        Returns:
            事件决策与原参数对象。
        """
        _ = event_name
        config = self._get_config()
        if not config.plugin.enabled or not config.plugin.enable_prompt_state_injection:
            return EventDecision.SUCCESS, params

        if str(params.get("name", "")) != config.plugin.target_prompt:
            return EventDecision.SUCCESS, params

        values = params.get("values")
        if not isinstance(values, dict):
            return EventDecision.SUCCESS, params

        stream_id = str(values.get("stream_id", ""))
        if not stream_id:
            return EventDecision.SUCCESS, params

        if config.plugin.private_only:
            try:
                stream_info = await get_stream_info(stream_id)
            except Exception as exc:
                logger.debug(f"获取 stream_info 失败 stream={stream_id[:8]}: {exc}")
                return EventDecision.SUCCESS, params
            if not stream_info or str(stream_info.get("chat_type", "")) != "private":
                return EventDecision.SUCCESS, params

        service = DFCKokoroStateService(plugin=self.plugin)
        injected = await service.render_prompt_state(stream_id)
        if not injected:
            return EventDecision.SUCCESS, params

        existing = str(values.get("extra", "") or "")
        values["extra"] = existing + "\n\n" + injected if existing else injected
        params["values"] = values

        if config.plugin.debug_log:
            logger.info(f"已向 DFC prompt 注入状态 stream={stream_id[:8]} len={len(injected)}")

        return EventDecision.SUCCESS, params
