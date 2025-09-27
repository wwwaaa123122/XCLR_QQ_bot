# 插件名称：AntiGroupInvite
# 功能：当检测到A群成员尝试拉机器人进入B群时，在A群中踢出该成员

TRIGGHT_KEYWORD = "Any"  # 永久触发插件，监听所有事件
HELP_MESSAGE = "自动处理拉群邀请保护插件 - 无需手动触发"

async def on_message(event, actions, Events, Manager, Segments):
    # 检查事件类型是否为群邀请事件
    if hasattr(Events, 'GroupInviteEvent') and isinstance(event, Events.GroupInviteEvent):
        # 获取邀请者的ID和群号
        inviter_id = event.user_id
        source_group_id = event.get('group_id')  # 可能需要根据实际事件结构调整
        
        # 确认这是从群内发起的邀请（而非私聊邀请）
        if source_group_id:
            # 在源群组中踢出邀请者
            await actions.kick_group_member(
                group_id=source_group_id,
                user_id=inviter_id
            )
            
            # 可选：发送踢人提示（如果需要可以取消注释）
            # kick_message = Manager.Message(
            #     Segments.Text(f"检测到违规拉群行为，已踢出用户{inviter_id}")
            # )
            # await actions.send(group_id=source_group_id, message=kick_message)
            
            return True  # 阻断后续插件处理此事件
    
    return False  # 不阻断其他插件