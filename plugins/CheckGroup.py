import json, aiohttp, uuid
from datetime import datetime

from Hyper import Configurator
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())
from Hyper import Listener

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "开群"
HELP_MESSAGE = f"{Configurator.cm.get_cfg().others['reminder']}开群 【群号码】 —> 打开该群的账户 👁"
WEBSOCKET_URL = f"ws://{Configurator.cm.get_cfg().connection.host}:{Configurator.cm.get_cfg().connection.port}"
# MAX_retry = 5
# retry_sleep = 1

async def get_group_info_from_ws(group_id):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WEBSOCKET_URL) as ws:
            request_id = str(uuid.uuid4())
            payload = {
                "action": "get_group_info",
                "params": {"group_id": group_id, "no_cache": True},
                "echo": request_id,
            }
            await ws.send_str(json.dumps(payload))

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    response_data = json.loads(msg.data)
                    if response_data.get("echo") == request_id:
                        return response_data.get("data")
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
    return None

async def on_message(event, actions: Listener.Actions, Manager, Segments,
                     order, bot_name, bot_name_en, ONE_SLOGAN, ADMINS, SUPERS, ROOT_User):
    # 动态获取发送目标（支持群聊和私聊）
    send_kwargs = {"message": None}
    is_group = hasattr(event, 'group_id') and event.group_id is not None
    if is_group:
        send_kwargs["group_id"] = event.group_id
    else:
        send_kwargs["user_id"] = event.user_id
    
    if order:
        uid_str = order[order.find(f"{TRIGGHT_KEYWORD} ") + len(f"{TRIGGHT_KEYWORD} "):].strip()
        if not uid_str:
            uid_str = event.group_id
        try:
            uid = int(uid_str)
        except (ValueError, TypeError):
            r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: {uid_str} 不是一个有效的群号码'''
            send_kwargs["message"] = Manager.Message(Segments.Text(r))
            await actions.send(**send_kwargs)
            return True

    try:
        group_info = await get_group_info_from_ws(uid)
        print(f"Debug: group_info type: {type(group_info)}, content: {group_info}")
    except Exception as e:
        print(f"get_group {uid} failed via websocket: {e}")
        r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: 获取群信息时出错: {e}'''
        send_kwargs["message"] = Manager.Message(Segments.Text(r))
        await actions.send(**send_kwargs)
        return True

    if not group_info:
        r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: 未能获取到 {uid} 的信息，可能 {uid} 不是一个有效的群号码，请稍后重试。'''
        print(f"get_group {uid} failed: no group_info returned")
        send_kwargs["message"] = Manager.Message(Segments.Text(r))
        await actions.send(**send_kwargs)
    elif isinstance(group_info, dict) and group_info.get("group_id"):
        r = parse_group_info(group_info, ADMINS, SUPERS, ROOT_User)
        print(f"get_group {uid} successfully")
        send_kwargs["message"] = Manager.Message(Segments.Text(r))
        await actions.send(**send_kwargs)
    else:
        r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: 返回的群组信息格式不正确。'''
        print(f"get_group {uid} failed: invalid group_info format: {type(group_info)} - {group_info}")
        send_kwargs["message"] = Manager.Message(Segments.Text(r))
        await actions.send(**send_kwargs)
        
    return True

def parse_group_info(group_dict, ADMINS, SUPERS, ROOT_User):
    try:
        result = f"""群名称: {group_dict.get('group_name', '未知')}
群号: {group_dict.get('group_id', '未知')}
群人数: {group_dict.get('member_count', '未知')}
人数上限: {group_dict.get('max_member_count', '未知')}"""

        return result

    except Exception as e:
        print(f"解析失败: {e}")
        return ("", "无法打开该群的信息")
