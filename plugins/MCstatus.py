import re
import aiohttp
from Hyper import Configurator

Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())
REMINDER = Configurator.cm.get_cfg().others["reminder"]

# 插件配置
IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "Any"
HELP_MESSAGE = f"{REMINDER}mc状态 <服务器地址> —> 查询MC服务器状态"

# 正则表达式
DOMAIN = re.compile(r"^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}|(?:\d{1,3}\.){3}\d{1,3})(?::\d+)?$")
IP = re.compile(r"\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b(?::\d{1,5})?")

EXPECTED_KEYWORDS = ["mc状态", "MC状态", "Mc状态", "我的世界状态", "minecraft状态", "java状态", "jv状态", "mcs"]

async def on_message(event, actions, Manager, Segments):
    user_msg = str(event.message).strip()

    if not user_msg.startswith(REMINDER):
        return

    user_msg = user_msg[len(REMINDER):].strip()

    if not any(kw in user_msg for kw in EXPECTED_KEYWORDS):
        return

    # 获取 group_id 或 user_id
    send_id = getattr(event, "group_id", None) or getattr(event, "user_id", None)

    # 去掉关键词，提取地址
    for kw in EXPECTED_KEYWORDS:
        user_msg = user_msg.replace(kw, "")
    msg = user_msg.strip()

    if msg == "":
        await actions.send(group_id=send_id,
                           message=Manager.Message(Segments.Text("请输入正确的域名或IP，支持带端口号")))
        return True

    # 检查域名或IP格式
    if not (DOMAIN.match(msg) or IP.match(msg)):
        await actions.send(group_id=send_id,
                           message=Manager.Message(Segments.Text("请输入正确的域名或IP，支持带端口号")))
        return True

    # 调用 API
    url = f"https://api.mcstatus.io/v2/status/java/{msg}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await actions.send(group_id=send_id,
                                       message=Manager.Message(Segments.Text("网络请求失败")))
                    return True
                data = await resp.json()

        # 拼接消息
        msglist = f"服务器地址：{msg}\n"
        if data.get("online"):
            msglist += "服务器状态：在线🟢\n"
        else:
            await actions.send(group_id=send_id,
                               message=Manager.Message(Segments.Text(f"服务器地址：{msg}\n服务器状态：离线🔴")))
            return True

        if data.get("eula_blocked") is True:
            msglist += "正版验证：开启\n"
        elif data.get("eula_blocked") is False:
            msglist += "正版验证：关闭\n"
        else:
            msglist += "正版验证：无法判断，请查看日志输出\n"

        msglist += f"版本：{data['version']['name_clean']}\n"
        msglist += f"介绍：\n{data['motd']['clean'].replace(' ', '')}\n"
        msglist += f"在线玩家数：{data['players']['online']}/{data['players']['max']}"

        # 发送图片或提示
        icon = data.get("icon")
        if icon and icon.startswith("data:image/png;base64,"):
            base64_img = icon.replace("data:image/png;base64,", "base64://")
            await actions.send(group_id=send_id,
                               message=Manager.Message([Segments.Image(base64_img), Segments.Text(msglist)]))
        elif icon is None:
            await actions.send(group_id=send_id,
                               message=Manager.Message(Segments.Text(f"[该服务器没有设置LOGO]\n{msglist}")))
        else:
            await actions.send(group_id=send_id,
                               message=Manager.Message(Segments.Text(f"[该服务器的LOGO无法识别]\n{msglist}")))

    except Exception as e:
        await actions.send(group_id=send_id,
                           message=Manager.Message(Segments.Text(f"发生错误：{e}")))
        return True

    return True
