# DFC Kokoro Bridge 验证说明

## 1. 启用插件

确认 [`plugins/dfc_kokoro_bridge/manifest.json`](../../../plugins/dfc_kokoro_bridge/manifest.json) 存在后启动应用。首次加载配置时会生成 [`config/plugins/dfc_kokoro_bridge/config.toml`](../../../config/plugins/dfc_kokoro_bridge/config.toml)。

## 2. 私聊状态注入验证

1. 在私聊里向 DFC 发送普通消息。
2. 诱导模型调用 [`record_inner_thought`](../../../plugins/dfc_kokoro_bridge/actions/record_inner_thought.py)。
3. 下一轮私聊触发 DFC。

预期：[`default_chatter_user_prompt`](../../../plugins/default_chatter/plugin.py:884) 的 [`values.extra`](../../../plugins/prompt_injector/event_handler.py:218) 中追加“私聊运行状态”，包含近期心理活动记录。

## 3. 回复等待验证

1. 让模型先调用 [`send_text`](../../../plugins/default_chatter/plugin.py:254) 发出一个需要对方回应的问题。
2. 同轮或后续调用 [`set_reply_wait`](../../../plugins/dfc_kokoro_bridge/actions/set_reply_wait.py)，设置较短等待时间。
3. 在等待期内回复，或等待超时。

预期：

- 用户提前回复时，等待状态被 [`DFCKokoroMessageObserver`](../../../plugins/dfc_kokoro_bridge/handlers/message_observer.py) 清除。
- 用户未回复且等待超时后，调度器通过 [`wake_stream()`](../../../plugins/dfc_kokoro_bridge/wake.py:30) 注入系统触发消息。

## 4. 预约思考验证

1. 调用 [`schedule_thought`](../../../plugins/dfc_kokoro_bridge/actions/schedule_thought.py)，测试时可把配置中的 `schedule_min_minutes` 调小。
2. 等待预约到期。

预期：到期后 [`DFCKokoroScheduler`](../../../plugins/dfc_kokoro_bridge/scheduler.py) 清除预约状态，并向私聊流注入“心理状态触发”消息，DFC 被唤醒后自然决策是否主动开口。

## 5. 沉默主动验证

1. 测试环境把 [`proactive.silence_threshold`](../../../plugins/dfc_kokoro_bridge/config.py) 调短。
2. 把 [`proactive.trigger_probability`](../../../plugins/dfc_kokoro_bridge/config.py) 设为 `1.0`。
3. 保持私聊沉默超过阈值。

预期：调度器触发沉默主动思考，并注入触发消息。
