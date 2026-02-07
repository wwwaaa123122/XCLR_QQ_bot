# 私聊插件快速参考

## 概览

以下 **10 个插件**已升级为支持私聊功能：

| 插件 | 触发词 | 功能 | 私聊用法 |
|------|--------|------|--------|
| **Ping** | `#ping` | Ping 域名/IP + 地理位置 | `#ping 1.1.1.1` |
| **ConvetToQR** | `#转码` | 文本/URL 转二维码 | `#转码 https://example.com` |
| **EncDecode** | `#enc解密` | 编码/解码工具 | `#enc解密 base64内容` |
| **CheckAccount** | `#开` | 查询 QQ 账户信息 | `#开 123456789` |
| **Like** | `超我/超市我` | 给名片点赞 | `超我` |
| **Hitokota** | `#一言` | 一句名言 | `#一言` |
| **Weather** | `#天气` | 城市天气查询 | `#天气 北京` |
| **MCstatus** | `#mc状态` | Minecraft 服务器状态 | `#mc状态 mc.example.com` |
| **whois** | `whois` | 域名信息查询 | `whois example.com` |
| **MelodyFetch** | `#点歌` | 音乐搜索和下载 | `#点歌 晴天` 或 `#点歌 ID` |

## 核心改动

每个插件都进行了以下修改：

### 1. 标记为私聊支持
```python
IS_PRIVATE_ENABLED = True
```

### 2. 兼容性发送逻辑
```python
# 群聊获取 group_id，私聊获取 user_id
send_id = getattr(event, "group_id", None) or getattr(event, "user_id", None)

# 或者两者都传（系统会自动选择）
await actions.send(group_id=getattr(event, "group_id", None), ...)
```

### 3. 完全向后兼容
- 所有插件在群聊中的行为保持不变
- 私聊中使用相同的触发词和参数
- 无需用户改变使用习惯

## 工作流程

```
私聊消息到达
    ↓
基本命令检查（ping, help, status 等）
    ↓
模式切换检查（Gemini, ChatGPT 等）
    ↓
插件执行（10 个已支持私聊的插件）
    ↓
[插件返回 True → 停止，不执行 AI 对话]
[插件返回 False/None → 继续执行 AI 对话]
```

## 调试信息

查看是否正确加载了私聊插件支持：

```python
# 在 main.py 中的插件执行部分
if hasattr(plugin, 'IS_PRIVATE_ENABLED') and plugin.IS_PRIVATE_ENABLED:
    # 该插件支持私聊
    pass
```

## 插件统计

- ✅ **已修改**: 10 个
- ⏭️ **可考虑修改**: 3 个（需要更复杂的改动）
- ❌ **不适合私聊**: 11 个（群聊特定功能）

## 常见问题

**Q: 私聊中的插件不工作？**
A: 检查：
1. 插件是否有 `IS_PRIVATE_ENABLED = True`
2. 触发词是否正确（某些需要前缀 `#`）
3. 查看后台日志了解执行情况

**Q: 插件在私聊中显示错误？**
A: 可能原因：
1. 插件中硬编码了 `event.group_id`（应使用 `getattr` 处理）
2. 某些 API 功能依赖群聊特性
3. 消息段不兼容（如 @提醒 在私聊中不存在）

**Q: 如何添加新的私聊插件？**
A: 参考 [PRIVATE_PLUGIN_GUIDE.md](PRIVATE_PLUGIN_GUIDE.md)

## 文件位置

```
/workspaces/XCLR_QQ_bot/
├── main.py                          # 核心系统
├── plugins/
│   ├── Ping.py                      ✅
│   ├── ConvetToQR.py                ✅
│   ├── EncDecode.py                 ✅
│   ├── CheckAccount.py              ✅
│   ├── Like.py                      ✅
│   ├── Hitokota.py                  ✅
│   ├── Weather.py                   ✅
│   ├── MCstatus.py                  ✅
│   ├── whois.py                     ✅
│   └── MelodyFetch.py               ✅
├── PLUGINS_PRIVATE_SUPPORT.md       # 详细列表
└── PRIVATE_PLUGIN_GUIDE.md          # 开发指南
```

## 测试命令

在私聊中试试这些命令：

```
#ping 8.8.8.8
#转码 https://github.com
#enc解密 aGVsbG8gd29ybGQ=
#开 123456789
超我
#一言
#天气 北京
#mc状态 mc.hypixel.net
whois github.com
#点歌 晴天
```

## 更新日志

### 当前版本
- ✅ 完成 10 个插件的私聊适配
- ✅ 所有修改都通过语法检查
- ✅ 保持完全向后兼容
- ✅ 创建完整的文档和参考

### 下一步计划
- [ ] 测试私聊中的实际功能
- [ ] 优化某些复杂插件（MelodyFetch）
- [ ] 考虑适配更多插件
