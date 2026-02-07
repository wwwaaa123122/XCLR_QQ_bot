# 私聊插件功能使用指南

## 功能概述

为私聊添加了**插件支持功能**。现在用户在私聊中可以触发**私聊专用插件**，且**无需添加 `reminder` 前缀**。

**重要提示：** 现有的大多数插件（如生图、涩图等）是为**群聊设计**的，它们在私聊中无法使用。只有**显式标记为支持私聊**的插件（通过 `IS_PRIVATE_ENABLED = True`）才能在私聊中被触发。

---

## 核心特性

### 1. **私聊专用插件**
- ✅ 在私聊中，私聊专用插件无需 `reminder` 前缀即可触发
- ✅ 直接输入插件关键词即可调用功能
- ✅ 需要显式声明 `IS_PRIVATE_ENABLED = True`

### 2. **插件兼容性**
- ❌ 群聊插件不支持在私聊中运行（自动被跳过）
- ✅ 私聊插件可以设计为仅在私聊中工作
- ✅ 避免属性错误（如 `event.group_id` 在私聊中不存在）

### 3. **灵活的触发方式**
- ✅ **有关键词的插件**：直接输入关键词触发
- ✅ **插件链式处理**：每个插件可选择是否继续后续处理

---

## 技术实现说明

### execute_plugins 函数修改

在 `main.py` 的 `execute_plugins()` 函数中新增 `is_private` 参数：

```python
async def execute_plugins(isAny: bool, is_private: bool = False, **main_context) -> bool:
```

**参数说明：**
- `isAny`：是否为 "Any" 模式（特殊的触发方式）
- `is_private`：是否为私聊模式，当为 `True` 时仅执行标记为 `IS_PRIVATE_ENABLED = True` 的插件

**触发逻辑：**
```
if is_private:
    # 私聊模式
    # 跳过不支持私聊的插件
    if not IS_PRIVATE_ENABLED:
        continue
    # 跳过空唤醒词（避免对所有消息都触发）
    if TRIGGHT_KEYWORD == "":
        continue
    # 支持关键词触发
    if TRIGGHT_KEYWORD in user_message:
        trigger = True
else:
    # 群聊模式（保持原逻辑）
    trigger = f"{reminder}{TRIGGHT_KEYWORD}" in f"{reminder}{user_message}"
```

### 私聊中的插件调用

在 [main.py L779](main.py#L779)：

```python
# 检查插件（私聊模式，仅执行标记为私聊专用的插件）
local_vars = globals().copy()
local_vars.update(locals().copy())
try:
    if await execute_plugins(False, is_private=True, **local_vars):
        return
except Exception as e:
    print(f"处理插件时发生错误: {e}")
    return
```

---

## 插件编写指南

### 最小示例（私聊专用）

```python
# -*- coding: utf-8 -*-

TRIGGHT_KEYWORD = "插件关键词"  # 在私聊中直接输入此词即可触发
HELP_MESSAGE = "插件简描 —> 详细描述"
IS_PRIVATE_ENABLED = True  # ⭐ 必须标记为支持私聊！

async def on_message(event, order: str) -> bool:
    """
    处理私聊消息
    
    返回 True 表示已处理，终止后续处理
    返回 False 或 None 表示未处理，继续执行后续逻辑
    """
    from Hyper.Events import PrivateMessageEvent
    
    if not isinstance(event, PrivateMessageEvent):
        return None
    
    # 处理逻辑
    print(f"插件触发！用户消息: {order}")
    
    return False  # 不拦截，继续执行
```

### 完整示例（私聊专用）

```python
# -*- coding: utf-8 -*-

TRIGGHT_KEYWORD = "查询"
HELP_MESSAGE = "查询功能 —> 查询相关信息"
IS_PRIVATE_ENABLED = True  # ⭐ 标记支持私聊

async def on_message(event, order: str) -> bool:
    from Hyper.Events import PrivateMessageEvent
    
    if not isinstance(event, PrivateMessageEvent):
        return None
    
    if order == "查询用户":
        # 处理查询逻辑
        return True
    
    return False
```

### ❌ 不推荐：空唤醒词（私聊中已禁用）

```python
# ❌ 不要这样写！私聊中空唤醒词已被禁用
TRIGGHT_KEYWORD = ""  # 在私聊中会被跳过
HELP_MESSAGE = "自动处理插件"
IS_PRIVATE_ENABLED = True

async def on_message(event, order: str) -> bool:
    # 这在私聊中永远不会被触发
    return False
```

这样写会避免触发，因为系统会自动跳过空唤醒词的插件。
    
    if not isinstance(event, PrivateMessageEvent):
        return None
    
    # 对消息进行预处理、记录、过滤等
    print(f"检测到消息: {order}")
    
    # 返回 False 表示不拦截，继续执行后续逻辑（如 AI 对话）
    # 返回 True 表示完全处理此消息，不再继续
    return False
```

### 完整功能示例（私聊自动回复）

详见 [plugins/PrivateAutoReply.py](plugins/PrivateAutoReply.py)

---

## 可用参数

在 `on_message()` 中，您可以使用以下参数（需要在函数签名中声明）：

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `event` | `Events.PrivateMessageEvent` | 消息事件对象 |
| `actions` | `Listener.Actions` | 消息操作接口 |
| `order` | `str` | 用户输入消息（已strip） |
| `user_message` | `str` | 原始用户消息 |
| `bot_name` | `str` | 机器人名称 |
| `event_user` | `str` | 用户昵称 |
| `sys_prompt` | `str` | 系统提示词 |
| `presets` | `dict` | 角色预设配置 |
| `config` | `Config` | 全局配置对象 |
| 其他 | - | main.py 中的全局变量 |

**提示：** 您只需声明需要的参数，不需要的参数可以省略。不建议使用 `**kwargs`，因为系统会自动提供所有需要的参数。

---

## 使用示例

### 场景1：指令触发
```python
TRIGGHT_KEYWORD = "查天气"

async def on_message(event, actions, order: str):
    from Hyper.Events import PrivateMessageEvent
    if isinstance(event, PrivateMessageEvent):
        # 获取天气信息
        weather = get_weather()
        await actions.send(user_id=event.user_id, message=weather)
        return True
    return None
```

用户在私聊输入 `查天气` 即可触发（无需前缀 `#`）

### 场景2：消息过滤
```python
TRIGGHT_KEYWORD = ""  # 空唤醒词

async def on_message(event, actions, order: str, **kwargs):
    from Hyper.Events import PrivateMessageEvent
    if isinstance(event, PrivateMessageEvent):
        # 检查是否包含敏感词
        if is_sensitive(order):
            await actions.send(user_id=event.user_id, 
                             message="包含违规内容")
            return True  # 拦截消息
    return False  # 不拦截，继续处理
```

对所有私聊消息进行检查

### 场景3：条件触发
```python
TRIGGHT_KEYWORD = "帮我"

async def on_message(event, actions, order: str, **kwargs):
    from Hyper.Events import PrivateMessageEvent
    if isinstance(event, PrivateMessageEvent):
        if "帮我" in order:
            # 处理帮助请求
            await actions.send(user_id=event.user_id, 
                             message="可以帮你...")
            return True
    return None
```

---

## 私聊与群聊插件的区别

| 特性 | 私聊 | 群聊 |
|------|------|------|
| Reminder 前缀 | ❌ 不需要 | ✅ 需要 |
| 空唤醒词 | ✅ 支持 | ❌ 不支持 |
| 关键词匹配 | 直接包含 | 需要前缀 |
| 消息目标 | 私聊 user_id | 群聊 group_id |

---

## 常见问题

**Q: 如何让插件只在私聊中工作？**
```python
from Hyper.Events import PrivateMessageEvent

async def on_message(event, ...):
    if not isinstance(event, PrivateMessageEvent):
        return None  # 不是私聊消息，跳过处理
    # 处理私聊逻辑
```

**Q: 空唤醒词插件会拦截 AI 对话吗？**
```python
# 不会，如果返回 False 或 None，继续执行后续 AI 对话
async def on_message(event, ...):
    if isinstance(event, PrivateMessageEvent):
        print(f"检测消息: {order}")
    return False  # 不拦截，继续 AI 处理
```

**Q: 多个空唤醒词插件会重复执行吗？**
是的。它们会按加载顺序执行，除非某个插件返回 `True` 来拦截后续处理。

**Q: 如何禁用某个插件？**
将插件文件名改为 `d_插件名.py` 即可禁用（前缀 `d_`）。

---

## 更新日志

### v1.0 (2025-01-24)
- ✨ 新增 `is_private` 参数支持
- ✨ 新增空唤醒词功能（`TRIGGHT_KEYWORD = ""`）
- ✨ 私聊插件无需 `reminder` 前缀
- ✨ 提供示例插件 [PrivateAutoReply.py](plugins/PrivateAutoReply.py)
- 📖 完整文档指南

---

## 相关文件

- [main.py](main.py) - 核心实现
- [PRIVATE_CHAT_FEATURE.md](PRIVATE_CHAT_FEATURE.md) - 私聊功能文档
- [plugins/PrivateAutoReply.py](plugins/PrivateAutoReply.py) - 示例插件
