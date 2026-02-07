# -*- coding: utf-8 -*-
"""
私聊自动回复插件示例
演示如何在私聊中使用基础插件功能
"""

# 插件配置
TRIGGHT_KEYWORD = "测试"  # 关键词 - 用户输入"测试"时触发
HELP_MESSAGE = "私聊自动回复 —> 测试插件功能"
IS_PRIVATE_ENABLED = True  # ✅ 标记此插件支持私聊


async def on_message(event, order: str) -> bool:
    """
    处理私聊消息的插件回调
    
    参数：
    - event: 消息事件对象
    - order: 用户输入的消息（去空格后）
    
    返回：
    - True: 表示已处理消息，后续不再调用其他插件或AI
    - False/None: 表示未处理，继续执行后续逻辑
    """
    
    # 只在私聊模式下运行
    from Hyper.Events import PrivateMessageEvent
    if not isinstance(event, PrivateMessageEvent):
        return None
    
    # 简单的日志记录
    print(f"[私聊插件] 用户 {event.user_id} 输入: {order}")
    
    # 返回 False 表示不拦截消息，继续执行后续逻辑（如AI对话）
    return False
