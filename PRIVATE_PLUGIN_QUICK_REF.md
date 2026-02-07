# 私聊插件快速参考

## 🚀 快速使用

### 创建最小插件

```python
# plugins/MyPlugin.py
TRIGGHT_KEYWORD = "关键词"  # 或 "" 用于空唤醒词
HELP_MESSAGE = "插件说明 —> 详细描述"

async def on_message(event, actions, order: str) -> bool:
    from Hyper.Events import PrivateMessageEvent
    if isinstance(event, PrivateMessageEvent):
        # 你的代码
        await actions.send(user_id=event.user_id, message="响应")
        return True  # 拦截 | False/None 继续处理
    return None
```

---

## 📋 关键概念

| 概念 | 说明 | 示例 |
|------|------|------|
| `TRIGGHT_KEYWORD` | 插件触发词 | `"查询"` 或 `""` |
| 空唤醒词 | 对所有消息触发 | `TRIGGHT_KEYWORD = ""` |
| `on_message()` | 处理函数 | 异步函数，返回 Bool |
| 返回 `True` | 拦截消息 | 终止后续处理 |
| 返回 `False/None` | 继续处理 | 继续调用后续插件或AI |

---

## 🔗 触发规则

### 群聊模式
```
用户输入: #weather      (需要 # 前缀)
TRIGGHT_KEYWORD: "weather"
条件: "#weather" in "#weather" ✅ 触发
```

### 私聊模式（新增）
```
用户输入: weather       (无需前缀)
TRIGGHT_KEYWORD: "weather"
条件: "weather" in "weather" ✅ 触发

用户输入: 任何内容
TRIGGHT_KEYWORD: "" 或 "EmptyTrigger"
条件: 空唤醒词 ✅ 总是触发
```

---

## 💡 常见场景

### 场景1：指令类插件
```python
TRIGGHT_KEYWORD = "帮助"

async def on_message(event, actions, order: str):
    from Hyper.Events import PrivateMessageEvent
    if isinstance(event, PrivateMessageEvent):
        help_text = "这是帮助信息..."
        await actions.send(user_id=event.user_id, message=help_text)
        return True  # 拦截，不继续处理
    return None
```
用户输入 `帮助` → 显示帮助 → 不继续

---

### 场景2：消息过滤插件
```python
TRIGGHT_KEYWORD = ""  # 空唤醒词

async def on_message(event, actions, order: str):
    from Hyper.Events import PrivateMessageEvent
    if isinstance(event, PrivateMessageEvent):
        if "敏感词" in order:
            await actions.send(user_id=event.user_id, message="违规内容")
            return True  # 拦截敏感消息
        return False  # 允许通过
    return None
```
所有消息 → 检查 → 拦截违规或继续

---

### 场景3：条件触发插件
```python
TRIGGHT_KEYWORD = "上"

async def on_message(event, actions, order: str):
    from Hyper.Events import PrivateMessageEvent
    if isinstance(event, PrivateMessageEvent):
        if "上传文件" in order:
            # 处理上传逻辑
            return True
        # 不是上传指令，继续处理
        return False
    return None
```

---

## 🔧 可用参数

在 `on_message()` 函数中可使用（只声明需要的参数）：

```python
async def on_message(
    event,              # PrivateMessageEvent 对象
    actions,            # 消息操作接口
    order: str,         # 用户消息（已strip）
    user_message: str,  # 原始消息（可选）
    bot_name: str,      # 机器人名称（可选）
    event_user: str,    # 用户昵称（可选）
) -> bool:
```

完整参数列表见：[PRIVATE_PLUGIN_GUIDE.md](PRIVATE_PLUGIN_GUIDE.md#可用参数)

---

## ❌ 常见错误

### ❌ 错误1：只处理群聊
```python
async def on_message(event, actions, order: str):
    # 无检查 → 会在群聊中触发！
    await actions.send(...)
```

### ✅ 正确做法
```python
async def on_message(event, actions, order: str):
    from Hyper.Events import PrivateMessageEvent
    if not isinstance(event, PrivateMessageEvent):
        return None  # ← 检查事件类型！
    # 处理私聊逻辑
```

---

### ❌ 错误2：关键词中包含前缀
```python
TRIGGHT_KEYWORD = "#查询"  # ✗ 错误
```

### ✅ 正确做法
```python
TRIGGHT_KEYWORD = "查询"  # ✓ 不包含 #
# 私聊时用户输入: 查询
# 群聊时用户输入: #查询
```

---

## 📝 完整示例

[plugins/PrivateAutoReply.py](../plugins/PrivateAutoReply.py)

---

## 🔗 更多资源

- 📖 [完整开发指南](PRIVATE_PLUGIN_GUIDE.md)
- 📖 [私聊功能文档](PRIVATE_CHAT_FEATURE.md)  
- 📄 [更新说明](PRIVATE_PLUGIN_UPDATE.md)

---

**提示：** 复制 `PrivateAutoReply.py` 修改后即可创建新插件！

