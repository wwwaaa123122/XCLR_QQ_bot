import aiohttp
from Hyper import Configurator
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "狐狸图"
HELP_MESSAGE = f"{Configurator.cm.get_cfg().others['reminder']}狐狸图 —> 随机拉一张狐狸图"

async def on_message(event, actions, Manager, Segments, bot_name):
    # 动态获取发送目标（支持群聊和私聊）
    send_kwargs = {"message": None}
    if getattr(event, 'group_id', None):
        send_kwargs["group_id"] = event.group_id
    else:
        send_kwargs["user_id"] = event.user_id
    
    try:

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("https://fpic.mcxclr.top") as response:
                if response.status == 200:
                    send_kwargs["message"] = Manager.Message([
                        Segments.Image(file="https://fpic.mcxclr.top")
                    ])
                    await actions.send(**send_kwargs)
                else:
                    send_kwargs["message"] = Manager.Message(Segments.Text(f"API请求失败，状态码: {response.status} - {bot_name}"))
                    await actions.send(**send_kwargs)

    except aiohttp.ClientError as e:
        send_kwargs["message"] = Manager.Message(Segments.Text(f"狐狸图API请求出错: {str(e)} - {bot_name}"))
        await actions.send(**send_kwargs)
    except Exception as e:
        send_kwargs["message"] = Manager.Message(Segments.Text(f"获取狐狸图图片时发生未知错误: {str(e)} - {bot_name}"))
        await actions.send(**send_kwargs)

    return True