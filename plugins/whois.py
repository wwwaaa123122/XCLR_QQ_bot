from Hyper import Configurator
import asyncio
import whois
from Hyper import Manager, Segments
from datetime import datetime

# 加载配置
Configurator.cm = Configurator.ConfigManager(
    Configurator.Config(file="config.json").load_from_file()
)

# 插件信息
TRIGGHT_KEYWORD = "Any"
HELP_MESSAGE = f"发送【whois example.com】可以查询域名注册信息（含中文翻译）"

def format_whois_info(domain: str) -> str:
    """获取并格式化 whois 信息"""
    try:
        w = whois.whois(domain)

        # 格式化结果
        info = []
        info.append(f"📄 Whois 查询结果 for {domain}")
        if w.domain_name:
            info.append(f"域名 (Domain): {w.domain_name}")
        if w.registrar:
            info.append(f"注册商 (Registrar): {w.registrar}")
        if w.creation_date:
            creation = w.creation_date
            if isinstance(creation, list):  # 有些库返回 list
                creation = creation[0]
            if isinstance(creation, datetime):
                creation = creation.strftime("%Y-%m-%d %H:%M:%S")
            info.append(f"创建时间 (Creation Date): {creation}")
        if w.updated_date:
            update = w.updated_date
            if isinstance(update, list):
                update = update[0]
            if isinstance(update, datetime):
                update = update.strftime("%Y-%m-%d %H:%M:%S")
            info.append(f"更新时间 (Updated Date): {update}")
        if w.expiration_date:
            expiry = w.expiration_date
            if isinstance(expiry, list):
                expiry = expiry[0]
            if isinstance(expiry, datetime):
                expiry = expiry.strftime("%Y-%m-%d %H:%M:%S")
            info.append(f"过期时间 (Expiry Date): {expiry}")
        if w.name_servers:
            ns = ", ".join(w.name_servers) if isinstance(w.name_servers, list) else w.name_servers
            info.append(f"域名服务器 (Name Servers): {ns}")
        if w.status:
            status = ", ".join(w.status) if isinstance(w.status, list) else w.status
            info.append(f"状态 (Status): {status}")

        return "\n".join(info) if info else "未能获取到有效的 Whois 信息。"

    except Exception as e:
        return f"Whois 查询失败: {str(e)}"

async def on_message(event, actions, Manager, Segments):
    if not hasattr(event, "message"):
        return False

    msg = str(event.message).strip()
    reminder = Configurator.cm.get_cfg().others["reminder"]

    if msg.startswith(f"{reminder}whois") or msg.startswith("whois"):
        parts = msg.split()
        if len(parts) < 2:
            await actions.send(
                group_id=getattr(event, "group_id", None),
                user_id=getattr(event, "user_id", None) if not hasattr(event, "group_id") else None,
                message=Manager.Message(Segments.Text("请输入要查询的域名，例如: whois example.com"))
            )
            return True

        domain = parts[1]
        result = format_whois_info(domain)

        # 限制输出长度，避免刷屏
        if len(result) > 1000:
            result = result[:1000] + "\n...结果过长已截断..."

        await actions.send(
            group_id=getattr(event, "group_id", None),
            user_id=getattr(event, "user_id", None) if not hasattr(event, "group_id") else None,
            message=Manager.Message(Segments.Text(result))
        )
        return True

    return False

print("[域名Whois插件] 已加载 ✅")
print("触发词: whois <域名>")
print("功能: 查询域名注册信息（自动解析，带中文翻译）")