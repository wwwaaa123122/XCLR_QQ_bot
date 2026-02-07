# 私聊插件功能更新说明

## 更新内容总结

为私聊功能添加了完整的插件支持，包括**空唤醒词**特性。用户现在可以在私聊中自由使用插件，无需添加 `reminder` 前缀。

---

## 核心改动

### 1. 修改 `execute_plugins()` 函数 [main.py L261-316](main.py#L261-L316)

**新增参数：** `is_private: bool = False`

**触发逻辑优化：**
```python
if is_private:
    # 私聊模式
    if plugin.TRIGGHT_KEYWORD == "" or plugin.TRIGGHT_KEYWORD == "EmptyTrigger":
        # 空唤醒词 → 对所有消息触发
        should_trigger = True
    elif plugin.TRIGGHT_KEYWORD in user_message:
        # 普通关键词 → 直接匹配（无需 # 前缀）
        should_trigger = True
else:
    # 群聊模式（保持原逻辑）
    should_trigger = f"{reminder}{keyword}" in message
```

### 2. 更新私聊插件调用 [main.py L761-769](main.py#L761-L769)

**改动前：**
```python
if await execute_plugins(False, **local_vars):
    return
```

**改动后：**
```python
if await execute_plugins(False, is_private=True, **local_vars):
    return
```

### 3. 增强帮助信息 [main.py L616-650](main.py#L616-L650)

在私聊帮助命令中新增【插件功能】部分，说明：
- ✨ 无需前缀即可调用插件
- ✨ 支持空唤醒词（输入任何内容都可触发）
- ✨ 支持直接输入插件关键词

---

## 新增文件

### 1. [PRIVATE_PLUGIN_GUIDE.md](PRIVATE_PLUGIN_GUIDE.md)
完整的私聊插件开发指南，包括：
- 功能概述和特性说明
- 技术实现细节
- 插件编写教程
- 代码示例（最小示例、空唤醒词示例、完整示例）
- 参数说明表
- 常见问题解答

### 2. [plugins/PrivateAutoReply.py](plugins/PrivateAutoReply.py)
示例插件，演示如何：
- 使用空唤醒词 `TRIGGHT_KEYWORD = ""`
- 在私聊中处理消息
- 返回值的含义（拦截 vs. 继续处理）

---

## 功能对比

| 特性 | 群聊 | 私聊（新） |
|------|------|----------|
| 插件支持 | ✅ | ✅ **新增** |
| Reminder 前缀 | ✅ 需要 | ❌ 不需要 |
| 空唤醒词 | ❌ | ✅ **新增** |
| 关键词触发 | `#keyword` | `keyword` |
| AI 对话 | ✅ | ✅ |
| 消息目标 | 群聊 group_id | 私聊 user_id |

---

## 使用示例

### 示例1：简单指令插件
```python
TRIGGHT_KEYWORD = "查天气"

async def on_message(event, actions, order: str, **kwargs):
    from Hyper.Events import PrivateMessageEvent
    if isinstance(event, PrivateMessageEvent):
        await actions.send(user_id=event.user_id, message="北京今日晴，25°C")
        return True
    return None
```
用户在私聊输入 `查天气` 即可触发（**无需 `#` 前缀**）

### 示例2：空唤醒词插件
```python
TRIGGHT_KEYWORD = ""  # 或 "EmptyTrigger"

async def on_message(event, actions, order: str, **kwargs):
    from Hyper.Events import PrivateMessageEvent
    if isinstance(event, PrivateMessageEvent):
        print(f"记录消息: {order}")
        return False  # 不拦截，继续AI处理
    return None
```
对**所有私聊消息**都会执行（例如：记录、过滤、分析）

---

## 向后兼容性

✅ **完全兼容现有代码**
- 群聊插件触发逻辑不变
- `execute_plugins()` 的 `is_private` 参数有默认值 `False`
- 所有现有调用无需修改

---

## 后续扩展建议

1. **权限控制** - 为不同用户的空唤醒词插件设置权限
2. **优先级系统** - 定义多个空唤醒词插件的执行顺序
3. **消息过滤链** - 构建消息预处理管道
4. **插件市场** - 为私聊专用插件创建分类库

---

## 文件列表

| 文件 | 类型 | 说明 |
|------|------|------|
| [main.py](main.py) | 修改 | 核心实现，新增 `is_private` 参数 |
| [PRIVATE_PLUGIN_GUIDE.md](PRIVATE_PLUGIN_GUIDE.md) | 新增 | 完整开发指南 |
| [plugins/PrivateAutoReply.py](plugins/PrivateAutoReply.py) | 新增 | 示例插件代码 |
| [PRIVATE_CHAT_FEATURE.md](PRIVATE_CHAT_FEATURE.md) | 现有 | 参考：私聊基础功能文档 |

---

## 快速开始

1. **创建插件** - 复制 `PrivateAutoReply.py` 作为模板
2. **修改关键词** - 设置 `TRIGGHT_KEYWORD` 为你的关键词（或留空使用空唤醒词）
3. **实现逻辑** - 在 `on_message()` 中编写处理代码
4. **测试** - 在私聊中输入关键词测试
5. **参考文档** - 详见 [PRIVATE_PLUGIN_GUIDE.md](PRIVATE_PLUGIN_GUIDE.md)

---

**版本：** 1.0  
**更新日期：** 2025-01-24  
**兼容性：** Python 3.8+
