TRIGGHT_KEYWORD = "Any"

async def on_message(event, actions, Events):
    # 检查事件类型是否为好友添加请求
    if isinstance(event, Events.FriendAddEvent):
        # 自动同意好友请求
        await actions.call_api(
            "set_friend_add_request",
            flag=event.flag,  # 请求的唯一标识
            approve=True,     # 同意请求
            remark=""         # 好友备注（留空使用默认）
        )
        return True  # 阻断后续插件处理这个事件
    
    return False  # 对于其他事件不阻断