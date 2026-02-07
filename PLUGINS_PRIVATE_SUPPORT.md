# 已启用私聊支持的插件列表

本文档列出了已经修改并支持私聊功能的所有插件。

## 修改说明

每个插件都进行了以下修改：

1. **添加 `IS_PRIVATE_ENABLED = True` 标记** - 告诉系统这个插件支持私聊
2. **修改发送逻辑** - 将硬编码的 `event.group_id` 改为支持 `user_id`（私聊）和 `group_id`（群聊）的兼容代码
3. **保持向后兼容** - 所有插件在群聊中的功能保持不变

## 已修改的插件

### 1. **Ping.py** ✅
- **功能**: Ping 域名/IP 并获取地理位置信息
- **修改内容**: 
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 消息发送已使用 `getattr(event, "group_id", None)` 处理可选参数
- **私聊中的用法**: `#ping 1.1.1.1`

### 2. **ConvetToQR.py** ✅
- **功能**: 将文本或URL转换为二维码
- **修改内容**:
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 修改发送逻辑使用 `send_id = getattr(event, "group_id", None) or getattr(event, "user_id", None)`
- **私聊中的用法**: `#转码 https://example.com`

### 3. **EncDecode.py** ✅
- **功能**: enc解密工具（Base64 + URL decode）
- **修改内容**:
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 修改所有发送调用为支持群聊/私聊的 `send_id`
- **私聊中的用法**: `#enc解密 编码内容`

### 4. **CheckAccount.py** ✅
- **功能**: 查询 QQ 账户信息（头像、签名、权限等）
- **修改内容**:
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 修改发送逻辑使用 `send_id = getattr(event, "group_id", None) or getattr(event, "user_id", None)`
  - 所有错误处理和成功消息都使用 `send_id`
- **私聊中的用法**: `#开 123456789`（直接输入 QQ 号）

### 5. **Like.py** ✅
- **功能**: 给用户 QQ 名片点赞（每天 10 次限制）
- **修改内容**:
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 已使用 `hasattr(event, "group_id")` 判断来兼容群聊/私聊
- **私聊中的用法**: 发送 `超我` 或 `超市我`

### 6. **Hitokota.py** ✅
- **功能**: 获取一句名言/句子
- **修改内容**:
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 修改发送调用为 `getattr(event, "group_id", None)` 和 `getattr(event, "user_id", None)`
- **私聊中的用法**: `#一言`

### 7. **Weather.py** ✅
- **功能**: 查询城市天气信息（今天、明天、后天）
- **修改内容**:
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 修改 `on_message` 函数使用 `send_id` 替代 `event.group_id`
  - 处理可选的 `message_id`（私聊中可能无法获取）
- **私聊中的用法**: `#天气 北京`

### 8. **MCstatus.py** ✅
- **功能**: 查询 Minecraft 服务器状态
- **修改内容**:
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 修改所有 `actions.send()` 调用使用 `send_id`
- **私聊中的用法**: `#mc状态 mc.example.com:25565`

### 9. **whois.py** ✅
- **功能**: 查询域名 WHOIS 信息
- **修改内容**:
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 已使用 `getattr(event, "group_id", None)` 和 `getattr(event, "user_id", None)` 进行兼容
- **私聊中的用法**: `whois example.com`

### 10. **MelodyFetch.py** ✅
- **功能**: 点歌/音乐搜索和下载（网易云）
- **修改内容**:
  - 添加 `IS_PRIVATE_ENABLED = True`
  - 修改 `on_message` 函数获取 `send_id`
  - 修改 `search_songs` 和 `get_song_by_id` 函数签名，添加 `send_id` 参数
  - 修改 `download_and_send_music` 函数添加 `send_id` 参数
  - 处理可选的 `message_id`
- **私聊中的用法**: 
  - `#点歌 晴天` - 搜索歌曲
  - `#点歌 2652820720` - 通过 ID 获取歌曲

## 未修改的插件（不适合私聊）

以下插件由于特性原因，不适合在私聊中使用，因此未进行修改：

- **GenerateFromACG.py** - 需要群聊转发消息，涉及复杂的 forward 消息处理
- **GenerateFromPixiv.py** - 涉及图片生成和群聊 forward 消息
- **Foxpic.py** - 图片内容，涉及群聊特性
- **GroupSummary.py** - 群聊总结，群聊专用功能
- **KuaishouAnalysis.py** - 快手分析，需要群聊环境
- **HeadImage.py** - 头像获取，实现简单但涉及群聊特定逻辑
- **AutoAcceptFriend.py** - 自动接受好友请求，bot 级别功能
- **Httptest.py** - 简单的 HTTP 测试工具
- **SoGood.py** - 点赞相关
- **QishuiMusic.py** - 与 MelodyFetch 相似但需要进一步检查

## 验证

所有修改的插件已通过 Python 语法检查：

```bash
python3 -m py_compile Ping.py ConvetToQR.py EncDecode.py CheckAccount.py \
  Like.py Hitokota.py Weather.py MCstatus.py whois.py MelodyFetch.py
```

## 说明

- 支持私聊的插件会在收到来自 `PrivateMessageEvent` 的消息时被触发
- 所有插件都保持了原有的群聊功能，完全向后兼容
- 在私聊中，这些插件会与 AI 对话功能正常协作
- 如果私聊消息匹配插件的触发词，插件会先执行，返回 `True` 会阻止 AI 对话

## 更新说明

这些插件的修改是为了支持新的私聊插件系统。核心改动包括：

1. `IS_PRIVATE_ENABLED = True` - 标记为支持私聊
2. 修改消息发送参数处理 - 支持 `group_id`（群聊）和 `user_id`（私聊）
3. 保持函数签名兼容性 - 添加新参数但保持现有功能不变
