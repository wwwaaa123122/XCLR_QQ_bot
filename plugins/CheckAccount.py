import json, aiohttp, uuid
import traceback
from datetime import datetime

from Hyper import Configurator
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())
from Hyper import Listener

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "开"
HELP_MESSAGE = f"{Configurator.cm.get_cfg().others['reminder']}开 【@一个用户/QQ号】 —> 打开该用户的账户 👁"

# 获取 WebSocket 连接配置
connection_config = Configurator.cm.get_cfg().connection
WEBSOCKET_HOST = connection_config.host
WEBSOCKET_PORT = connection_config.port
SATORI_TOKEN = getattr(connection_config, 'satori_token', '') or getattr(connection_config, 'access_token', '')

# 构建 WebSocket URL，支持 token
if SATORI_TOKEN:
    WEBSOCKET_URL = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/?token={SATORI_TOKEN}"
else:
    WEBSOCKET_URL = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}"

# MAX_retry = 5
# retry_sleep = 1

async def get_user_info_from_ws(user_id):
    headers = {}
    if SATORI_TOKEN:
        headers["Authorization"] = f"Bearer {SATORI_TOKEN}"
    
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WEBSOCKET_URL, headers=headers) as ws:
            request_id = str(uuid.uuid4())
            payload = {
                "action": "get_stranger_info",
                "params": {"user_id": user_id, "no_cache": True},
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

# async def on_message(event, actions: Listener.Actions, Manager, Segments, 
#                      order, bot_name, bot_name_en, ONE_SLOGAN, ADMINS, SUPERS, ROOT_User):
#     uid = 0
#     for i in event.message:
#         if isinstance(i, Segments.At):
#             uid = int(i.qq)
#             break
        
#     if uid == 0:
#         uid = order[order.find(f"{TRIGGHT_KEYWORD} ") + len(f"{TRIGGHT_KEYWORD} "):].strip()
        
#     retry_time = 0
#     while True:
#         retry_time += 1
#         print(f"try to get_user {uid} time: {retry_time}")

#         gc.collect()
#         nikename = Manager.Ret.fetch(await actions.custom.get_stranger_info(user_id=uid, no_cache=True)).data.raw
#         if len(nikename) == 0:
#             r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
# ————————————————————
# 失败: {uid} 不是一个有效的用户'''
#             print(f"get_user {uid} failed: didn't found user")
#             await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text(r)))
#             break

#         else:
#             if str(nikename.get('user_id', '未知')) == str(uid):
#                 avatar, r = parse_user_info(nikename, ADMINS, SUPERS, ROOT_User)
#                 print(f"get_user {uid} successfully")
#                 await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Image(avatar), Segments.Text(r)))
#                 break
#             else:
#                 if retry_time > MAX_retry:
#                     print(f"get_user {uid} failed: max retry")
#                     r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
# ————————————————————
# 失败: 在 {MAX_retry} 次尝试连接服务器后，未能找到 {uid} 的信息'''
#                     await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text(r)))
#                     break
#                 else:
#                     time.sleep(retry_sleep)
        
#     return True

async def get_user_info_from_ws(user_id):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WEBSOCKET_URL) as ws:
            request_id = str(uuid.uuid4())
            payload = {
                "action": "get_stranger_info",
                "params": {"user_id": user_id, "no_cache": True},
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
    if hasattr(event, 'group_id') and event.group_id is not None:
        send_kwargs["group_id"] = event.group_id
    else:
        send_kwargs["user_id"] = event.user_id
    
    uid = 0
    for i in event.message:
        if isinstance(i, Segments.At):
            uid = int(i.qq)
            break

    if uid == 0:
        uid_str = order[order.find(f"{TRIGGHT_KEYWORD} ") + len(f"{TRIGGHT_KEYWORD} "):].strip()
        if not uid_str:
            uid_str = event.user_id
        try:
            uid = int(uid_str)
        except (ValueError, TypeError):
            r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: {uid_str} 不是一个有效的用户'''
            send_kwargs["message"] = Manager.Message(Segments.Text(r))
            await actions.send(**send_kwargs)
            return True

    try:
        user_info = await get_user_info_from_ws(uid)
        print(f"Debug: user_info type: {type(user_info)}, content: {user_info}")
    except Exception as e:
        print(f"get_user {uid} failed via websocket: {e}")
        r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: 获取用户信息时出错: {e}'''
        send_kwargs["message"] = Manager.Message(Segments.Text(r))
        await actions.send(**send_kwargs)
        return True

    if not user_info:
        r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: 未能获取到 {uid} 的信息，可能 {uid} 不是一个有效的用户，请稍后重试。'''
        print(f"get_user {uid} failed: no user_info returned")
        send_kwargs["message"] = Manager.Message(Segments.Text(r))
        await actions.send(**send_kwargs)
    elif isinstance(user_info, dict) and user_info.get("user_id"):
        framework = await actions.get_version_info()
        framework = framework.data.raw
        if "NapCat" in framework.get("app_name"):
            avatar, r = parser_user_info_napcat(user_info, ADMINS, SUPERS, ROOT_User)
        else:
            avatar, r = parse_user_info(user_info, ADMINS, SUPERS, ROOT_User)
        print(f"get_user {uid} successfully")
        if avatar:
            send_kwargs["message"] = Manager.Message(Segments.Image(avatar), Segments.Text(r))
            await actions.send(**send_kwargs)
        else:
            send_kwargs["message"] = Manager.Message(Segments.Text(r))
            await actions.send(**send_kwargs)
    else:
        r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: 返回的用户信息格式不正确。'''
        print(f"get_user {uid} failed: invalid user_info format: {type(user_info)} - {user_info}")
        send_kwargs["message"] = Manager.Message(Segments.Text(r))
        await actions.send(**send_kwargs)
        
    return True

def parser_user_info_napcat(user_dict, ADMINS, SUPERS, ROOT_User):
    try:
        avatar = user_dict.get('avatar', '')
        register_time = user_dict.get('reg_time', '')
        try:
            dt = datetime.strptime(register_time, '%Y-%m-%dT%H:%M:%SZ')
            register_time = dt.strftime('%Y.%m.%d %H:%M:%S')
        except (ValueError, TypeError):
            register_time = '未知时间'
            
        is_vip = user_dict.get('is_vip', False)
        vip_level = user_dict.get('vip_level', 0)
        is_year_vip = user_dict.get('is_years_vip', False)

        status_msg = "(框架不支持)" # NapCat not support
        if str(user_dict.get('user_id', '未知')) in ROOT_User:
            status_user = "ROOT_User"
        elif str(user_dict.get('user_id', '未知')) in SUPERS:
            status_user = "Super_User"
        elif str(user_dict.get('user_id', '未知')) in ADMINS:
            status_user = "Manage_User"
        else:
            status_user = "普通用户"
            
        result = f"""昵称: {user_dict.get('nickname', '未知')}
状态: {status_msg}
QQ号: {user_dict.get('uin', '未知')}
QID: {user_dict.get('qid', '未知')}
性别: {'男' if user_dict.get('sex') == 'male' else '女'}
年龄: {user_dict.get('age', '未知')}
权限: {status_user}
QQ等级: {user_dict.get('qqLevel', '未知')}
个性签名: {user_dict.get('longNick', '暂无签名')}
注册时间: {register_time}
超级会员: {'是' if is_vip else '否'}
会员等级: {vip_level}
年费会员: {'是' if is_year_vip else '否'}"""

        return (avatar, result)

    except Exception as e:
        print(f"解析失败: {traceback.format_exc()}")
        return ("", "无法打开该用户的账户")

def parse_user_info(user_dict, ADMINS, SUPERS, ROOT_User):
    try:
        avatar = user_dict.get('avatar', '')
        register_time = user_dict.get('RegisterTime', '')
        try:
            dt = datetime.strptime(register_time, '%Y-%m-%dT%H:%M:%SZ')
            register_time = dt.strftime('%Y.%m.%d %H:%M:%S')
        except (ValueError, TypeError):
            register_time = '未知时间'
            
        business = user_dict.get('Business', [])
        is_vip = any(item.get('type') == 1 for item in business)
        vip_level = next((item.get('level', 0) for item in business if item.get('type') == 1), 0)
        is_year_vip = any(item.get('isyear') == 1 for item in business if item.get('type') == 1)

        status_msg = user_dict.get('status', {}).get('message', '暂无状态')
        if str(user_dict.get('user_id', '未知')) in ROOT_User:
            status_user = "ROOT_User"
        elif str(user_dict.get('user_id', '未知')) in SUPERS:
            status_user = "Super_User"
        elif str(user_dict.get('user_id', '未知')) in ADMINS:
            status_user = "Manage_User"
        else:
            status_user = "普通用户"
            
        result = f"""昵称: {user_dict.get('nickname', '未知')}
状态: {status_msg}
QQ号: {user_dict.get('user_id', '未知')}
QID: {user_dict.get('q_id', '未知')}
性别: {'男' if user_dict.get('sex') == 'male' else '女'}
年龄: {user_dict.get('age', '未知')}
权限: {status_user}
QQ等级: {user_dict.get('level', '未知')}
个性签名: {user_dict.get('sign', '暂无签名')}
注册时间: {register_time}
超级会员: {'是' if is_vip else '否'}
会员等级: {vip_level}
年费会员: {'是' if is_year_vip else '否'}"""

        return (avatar, result)

    except Exception as e:
        print(f"解析失败: {traceback.format_exc()}")
        return ("", "无法打开该用户的账户")