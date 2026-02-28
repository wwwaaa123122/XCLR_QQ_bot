import aiohttp
from Hyper import Configurator

Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "转码 "
HELP_MESSAGE = f"{Configurator.cm.get_cfg().others['reminder']}转码 url/文本 —> 生成二维码图片"

HEADERS = {
    'User-Agent': 'xiaoxiaoapi/1.0.0 (https://xxapi.cn)'
}

API_URL = "https://v2.xxapi.cn/api/qrcode"

async def on_message(event, actions, Manager, Segments):
    msg = str(event.message).strip()
    reminder = Configurator.cm.get_cfg().others["reminder"]
    
    # 判断是否是群聊
    is_group = hasattr(event, 'group_id') and event.group_id is not None
    
    # 群聊模式需要 reminder 前缀，私聊模式不需要
    if is_group:
        prefix = f"{reminder}{TRIGGHT_KEYWORD}"
        if not msg.startswith(prefix):
            return False
        text = msg[len(prefix):].strip()
    else:
        # 私聊模式：支持"转码 xxx"格式
        if msg.startswith("转码 "):
            text = msg[len("转码 "):].strip()
        elif msg.startswith(f"{reminder}转码 "):
            text = msg[len(f"{reminder}转码 "):].strip()
        else:
            return False
    
    # 动态获取发送目标（支持群聊和私聊）
    send_kwargs = {"message": None}
    if is_group:
        send_kwargs["group_id"] = event.group_id
    else:
        send_kwargs["user_id"] = event.user_id
    
    if not text:
        send_kwargs["message"] = Manager.Message(Segments.Text("请在'转码'后输入需要生成二维码的内容，如网址或文本~"))
        await actions.send(**send_kwargs)
        return True
    params = {"text": text}
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(API_URL, params=params) as resp:
                data = await resp.json()
                if str(data.get('code')) == '200' and 'data' in data:
                    img_url = data['data']
                    send_kwargs["message"] = Manager.Message(Segments.Image(img_url))
                    await actions.send(**send_kwargs)
                else:
                    send_kwargs["message"] = Manager.Message(Segments.Text("二维码生成失败，请稍后再试~"))
                    await actions.send(**send_kwargs)
    except Exception as e:
        send_kwargs["message"] = Manager.Message(Segments.Text(f"请求出错：{e}"))
        await actions.send(**send_kwargs)
    return True
