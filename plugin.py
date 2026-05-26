"""DFC Kokoro Bridge 插件入口。

插件以旁路形式增强 default_chatter 的私聊体验：提供内心记录、回复等待、
预约思考、运行时状态注入和主动唤醒能力，不修改框架源码和 default_chatter。
"""

from __future__ import annotations

from src.app.plugin_system.api.action_api import clear_schema_cache
from src.app.plugin_system.api.log_api import get_logger
from src.app.plugin_system.base import BasePlugin, register_plugin

from .actions.schedule_thought import ScheduleThoughtAction
from .actions.set_reply_wait import SetReplyWaitAction
from .config import DFCKokoroBridgeConfig
from .handlers.message_observer import DFCKokoroMessageObserver
from .handlers.prompt_state_injector import DFCKokoroPromptStateInjector
from .scheduler import DFCKokoroScheduler
from .services.state_service import DFCKokoroStateService
from .store import BridgeSessionStore

logger = get_logger("dfc_kokoro_bridge.plugin")


@register_plugin
class DFCKokoroBridgePlugin(BasePlugin):
    """DefaultChatter 私聊心理增强桥接插件。"""

    plugin_name: str = "dfc_kokoro_bridge"
    plugin_description: str = "为 default_chatter 提供 KFC 风格的私聊心理状态、回复等待、预约思考与主动唤醒"
    plugin_version: str = "1.0.0"
    plugin_author: str = "MoFox Team"

    configs: list[type] = [DFCKokoroBridgeConfig]
    dependent_components: list[str] = ["default_chatter:chatter:default_chatter"]

    session_store: BridgeSessionStore
    scheduler: DFCKokoroScheduler

    def __init__(self, config: object | None = None) -> None:
        """初始化插件实例。

        Args:
            config: 插件配置实例。
        """
        super().__init__(config)  # type: ignore[arg-type]
        effective_config = self._get_config()
        self.session_store = BridgeSessionStore(max_entries=effective_config.mental.max_log_entries)
        self.scheduler = DFCKokoroScheduler(effective_config, self.session_store)
        self._sync_action_descriptions(effective_config)

    def _get_config(self) -> DFCKokoroBridgeConfig:
        """获取有效配置对象。"""
        if isinstance(self.config, DFCKokoroBridgeConfig):
            return self.config
        return DFCKokoroBridgeConfig()

    def get_components(self) -> list[type]:
        """返回插件包含的组件类。"""
        config = self._get_config()
        if not config.plugin.enabled:
            logger.info("dfc_kokoro_bridge 已在配置中禁用")
            return []

        return [
            ScheduleThoughtAction,
            SetReplyWaitAction,
            DFCKokoroPromptStateInjector,
            DFCKokoroMessageObserver,
            DFCKokoroStateService,
        ]

    async def on_plugin_loaded(self) -> None:
        """插件加载后刷新 Action 文案并启动调度检查。"""
        config = self._get_config()
        if not config.plugin.enabled:
            return
        self._sync_action_descriptions(config)
        await self.scheduler.start()

    def _sync_action_descriptions(self, config: DFCKokoroBridgeConfig) -> None:
        """把配置中的工具提示词同步到 Action 类描述并清理 schema 缓存。"""
        SetReplyWaitAction.action_description = config.action_prompt.set_reply_wait_description
        schedule_parts = [config.action_prompt.schedule_thought_description.strip()]
        guidance = config.action_prompt.schedule_guidance.strip()
        if guidance:
            schedule_parts.append(guidance)
        ScheduleThoughtAction.action_description = "\n\n".join(part for part in schedule_parts if part)
        clear_schema_cache("dfc_kokoro_bridge:action:set_reply_wait")
        clear_schema_cache("dfc_kokoro_bridge:action:schedule_thought")

    async def on_plugin_unloaded(self) -> None:
        """插件卸载时移除调度任务。"""
        await self.scheduler.stop()
