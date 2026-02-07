import json, aiohttp, uuid
from datetime import datetime

from Hyper import Configurator
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())
from Hyper import Listener

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "开"
HELP_MESSAGE = f"{Configurator.cm.get_cfg().others['reminder']}开 【@一个用户/QQ号】 —> 打开该用户的账户 👁"
WEBSOCKET_URL = f"ws://{Configurator.cm.get_cfg().connection.host}:{Configurator.cm.get_cfg().connection.port}"

# NapCat 配置
NAPCAT_API_VERSION = "v11"  # NapCat 使用 OneBot v11 协议
# MAX_retry = 5
# retry_sleep = 1

async def get_user_info_from_ws(user_id):
    """NapCat 兼容的获取用户信息函数"""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WEBSOCKET_URL) as ws:
            request_id = str(uuid.uuid4())
            # NapCat OneBot v11 兼容的 API 调用格式
            payload = {
                "action": "get_stranger_info",
                "params": {
                    "user_id": int(user_id), 
                    "no_cache": True
                },
                "echo": request_id,
            }
            await ws.send_str(json.dumps(payload))

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    response_data = json.loads(msg.data)
                    if response_data.get("echo") == request_id:
                        # NapCat 响应格式可能不同，适配处理
                        if response_data.get("status") == "ok":
                            return response_data.get("data")
                        else:
                            # 尝试旧格式兼容
                            return response_data.get("data")
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
    return None

async def get_user_info_from_actions(actions, user_id):
    """使用 actions 对象获取用户信息（NapCat 推荐方式）"""
    try:
        # 优先使用 NapCat 的 actions API
        result = await actions.call_api(
            "get_stranger_info",
            user_id=int(user_id),
            no_cache=True
        )
        
        # 检查返回结果格式
        if isinstance(result, dict):
            if result.get("status") == "ok" and result.get("data"):
                return result["data"]
            elif result.get("user_id"):  # 直接返回用户数据
                return result
        
        # 如果格式不匹配，尝试返回原始结果
        return result
        
    except Exception as e:
        print(f"actions API 获取用户信息失败: {e}")
        return None



async def get_user_info_from_actions(actions, user_id):
    """使用 actions 对象获取用户信息（NapCat 推荐方式）"""
    try:
        # 优先使用 NapCat 的 actions API
        result = await actions.call_api(
            "get_stranger_info",
            user_id=int(user_id),
            no_cache=True
        )
        
        # 检查返回结果格式
        if isinstance(result, dict):
            if result.get("status") == "ok" and result.get("data"):
                return result["data"]
            elif result.get("user_id"):  # 直接返回用户数据
                return result
        
        # 如果格式不匹配，尝试返回原始结果
        return result
        
    except Exception as e:
        print(f"actions API 获取用户信息失败: {e}")
        return None


async def on_message(event, actions: Listener.Actions, Manager, Segments,
                     order, bot_name, bot_name_en, ONE_SLOGAN, ADMINS, SUPERS, ROOT_User):
    # 获取 group_id 或 user_id
    send_id = getattr(event, "group_id", None) or getattr(event, "user_id", None)
    
    uid = 0
    for i in event.message:
        if isinstance(i, Segments.At):
            uid = int(i.qq)
            break

    if uid == 0:
        uid_str = order[order.find(f"{TRIGGHT_KEYWORD} ") + len(f"{TRIGGHT_KEYWORD} "):].strip()
        try:
            uid = int(uid_str)
        except (ValueError, TypeError):
            r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: {uid_str} 不是一个有效的用户'''
            await actions.send(group_id=send_id, message=Manager.Message(Segments.Text(r)))
            return True

    # NapCat 兼容的多重获取策略
    user_info = None
    
    # 方法1: 优先使用 actions API (NapCat 推荐)
    try:
        user_info = await get_user_info_from_actions(actions, uid)
        if user_info:
            print(f"Debug: 使用 actions API 获取用户信息成功: {type(user_info)}")
        else:
            print("Debug: actions API 返回空结果，尝试 WebSocket")
    except Exception as e:
        print(f"Debug: actions API 失败，尝试 WebSocket: {e}")
    
    # 方法2: 备用 WebSocket 连接
    if not user_info:
        try:
            user_info = await get_user_info_from_ws(uid)
            print(f"Debug: 使用 WebSocket 获取用户信息: {type(user_info)}, content: {user_info}")
        except Exception as e:
            print(f"get_user {uid} failed via websocket: {e}")
            r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: 获取用户信息时出错: {e}'''
            await actions.send(group_id=send_id, message=Manager.Message(Segments.Text(r)))
            return True

    # 处理获取到的用户信息
    if not user_info:
        r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: 未能获取到 {uid} 的信息，可能 {uid} 不是一个有效的用户，请稍后重试。'''
        print(f"get_user {uid} failed: no user_info returned")
        await actions.send(group_id=send_id, message=Manager.Message(Segments.Text(r)))
    elif isinstance(user_info, dict) and user_info.get("user_id"):
        avatar, r = parse_user_info(user_info, ADMINS, SUPERS, ROOT_User)
        print(f"get_user {uid} successfully")
        
        # NapCat 兼容的消息发送
        try:
            # 构建消息段
            message_parts = []
            if avatar:
                message_parts.append(Segments.Image(avatar))
            message_parts.append(Segments.Text(r))
            
            await actions.send(group_id=send_id, message=Manager.Message(*message_parts))
        except Exception as e:
            print(f"发送消息失败: {e}")
            # 备用发送方式
            await actions.send(group_id=send_id, message=Manager.Message(Segments.Text(r)))
    else:
        r = f'''{bot_name} {bot_name_en} - {ONE_SLOGAN}
————————————————————
失败: 返回的用户信息格式不正确。'''
        print(f"get_user {uid} failed: invalid user_info format: {type(user_info)} - {user_info}")
        await actions.send(group_id=send_id, message=Manager.Message(Segments.Text(r)))
        
    return True

def parse_user_info(user_dict, ADMINS, SUPERS, ROOT_User):
    """NapCat 兼容的用户信息解析函数"""
    try:
        # NapCat 可能返回不同的头像字段名
        avatar = user_dict.get('avatar') or user_dict.get('face') or user_dict.get('head_img') or ''
        
        # NapCat 可能使用不同的注册时间字段名
        register_time = (user_dict.get('RegisterTime') or 
                        user_dict.get('register_time') or 
                        user_dict.get('join_time') or '')
        
        # 处理时间格式
        try:
            if register_time:
                dt = datetime.strptime(register_time, '%Y-%m-%dT%H:%M:%SZ')
                register_time = dt.strftime('%Y.%m.%d %H:%M:%S')
            else:
                register_time = '未知时间'
        except (ValueError, TypeError):
            try:
                # 尝试其他可能的时间格式
                if register_time:
                    dt = datetime.fromtimestamp(int(register_time))
                    register_time = dt.strftime('%Y.%m.%d %H:%M:%S')
                else:
                    register_time = '未知时间'
            except (ValueError, TypeError):
                register_time = '未知时间'
            
        # NapCat 的会员信息可能在不同字段
        business = user_dict.get('Business') or user_dict.get('vip_info') or []
        is_vip = any(item.get('type') == 1 for item in business if isinstance(item, dict))
        vip_level = next((item.get('level', 0) for item in business if isinstance(item, dict) and item.get('type') == 1), 0)
        is_year_vip = any(item.get('isyear') == 1 for item in business if isinstance(item, dict) and item.get('type') == 1)

        # NapCat 可能使用不同的状态字段
        status_msg = (user_dict.get('status', {}).get('message') if user_dict.get('status') else None) or \
                    user_dict.get('liveness') or \
                    user_dict.get('status_desc') or \
                    '暂无状态'
        
        # 权限状态判断
        user_id_str = str(user_dict.get('user_id', '未知'))
        if user_id_str in ROOT_User:
            status_user = "ROOT_User"
        elif user_id_str in SUPERS:
            status_user = "Super_User"
        elif user_id_str in ADMINS:
            status_user = "Manage_User"
        else:
            status_user = "普通用户"
        
        # NapCat 兼容的字段映射
        nickname = user_dict.get('nickname') or user_dict.get('card') or user_dict.get('name') or '未知'
        qid = user_dict.get('q_id') or user_dict.get('qid') or '未知'
        sex = user_dict.get('sex') or 'unknown'
        if sex == 'male' or sex == '男':
            sex_display = '男'
        elif sex == 'female' or sex == '女':
            sex_display = '女'
        else:
            sex_display = '未知'
            
        age = user_dict.get('age') or '未知'
        level = user_dict.get('level') or user_dict.get('qq_level') or '未知'
        sign = user_dict.get('sign') or user_dict.get('signature') or '暂无签名'
            
        result = f"""昵称: {nickname}
状态: {status_msg}
QQ号: {user_dict.get('user_id', '未知')}
QID: {qid}
性别: {sex_display}
年龄: {age}
权限: {status_user}
QQ等级: {level}
个性签名: {sign}
注册时间: {register_time}
超级会员: {'是' if is_vip else '否'}
会员等级: {vip_level}
年费会员: {'是' if is_year_vip else '否'}"""

        return (avatar, result)

    except Exception as e:
        print(f"解析失败: {e}")
        # 返回简化版本，即使解析失败也显示基本信息
        try:
            user_id = user_dict.get('user_id', '未知')
            nickname = user_dict.get('nickname', '未知')
            result = f"基本信息:\nQQ号: {user_id}\n昵称: {nickname}\n\n(部分信息解析失败)"
            return ("", result)
        except:
            return ("", "无法打开该用户的账户")
