# DFC Kokoro Bridge

**DFC Kokoro Bridge** 是一个为 Neo-MoFox 框架中的 `default_chatter` (DFC) 量身定制的“旁路增强”插件。它旨在不修改 DFC 源码的前提下，为其提供类似 KokoroFlowChatter (KFC) 的高级私聊心理状态管理能力。

## 核心功能

- **运行时状态注入**：通过 `on_prompt_build` 事件，将私聊的实时状态（如等待剩余时间、预约信息、触发原因、近期心理活动）注入 DFC 的 User Prompt。
- **回复等待 (Reply Wait)**：允许模型在发完消息后登记“心理等待”状态。支持三阶段引导提示和硬性连续超时限制。
- **预约思考 (Scheduled Thought)**：允许模型预约未来某个时间点的主动唤醒，用于维持长线联系节律。
- **主动触发 (Proactive Trigger)**：在私聊沉默较久时，根据概率和勿扰时段自动唤醒模型。
- **心理日志 (Mental Log)**：记录模型在调用 Bridge 工具时的内心思考，并在后续对话中作为上下文参考。

## 快速开始

1. 确保已安装并启用 `default_chatter` 插件。
2. 将本插件放入 `plugins` 目录。
3. 插件会自动识别私聊环境并向 DFC 暴露以下工具：
   - `set_reply_wait`: 设置回复等待。
   - `schedule_thought`: 预约下一次主动思考。
   - `record_inner_thought`: 记录纯粹的内心活动。

## 配置说明

配置文件位于 `config/plugins/dfc_kokoro_bridge/config.toml`。

### 关键配置项

- `[wait]`:
  - `max_consecutive_timeouts`: 连续超时上限（默认 3）。达到上限后将强制结束等待。
  - `timeout_stage_X_prompt`: 各阶段的引导提示词，支持自定义。
- `[proactive]`:
  - `silence_threshold`: 沉默触发阈值（秒）。
  - `quiet_hours_start/end`: 勿扰时段。
  - `wake_cold_stream`: 预约到期时是否允许冷启动流循环。

## 设计哲学

本插件遵循“外科手术式增强”原则：
- **零侵入**：不修改框架核心代码，不修改 DFC 代码。
- **状态隔离**：Bridge 维护独立于 DFC 的 Session 状态，仅在 Prompt 构建阶段进行事实注入。
- **私聊专用**：所有 Bridge 工具和状态注入仅在私聊（Private Chat）中生效。

## 开发者

- **Author**: MoFox Team
- **Version**: 1.0.0
