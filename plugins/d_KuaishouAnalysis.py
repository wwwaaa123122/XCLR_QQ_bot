import re
import aiohttp
import asyncio
import os
import requests
from Hyper import Configurator

# 预编译正则表达式
_KUAISHOU_PATTERN = re.compile(r'(https?://v\.kuaishou\.com/[^\s]+|https?://www\.kuaishou\.com/[^\s]+)')

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "Any"

# 白名单文件路径
_WHITELIST_FILE = "kuaishou_whitelist.txt"

# 初始化白名单集合
_whitelist = set()

# 加载白名单
def _load_whitelist():
    global _whitelist
    if os.path.exists(_WHITELIST_FILE):
        with open(_WHITELIST_FILE, "r", encoding="utf-8") as f:
            _whitelist = set(line.strip() for line in f if line.strip())

# 保存白名单
def _save_whitelist():
    with open(_WHITELIST_FILE, "w", encoding="utf-8") as f:
        for group_id in _whitelist:
            f.write(f"{group_id}\n")

# 初始化时加载白名单
_load_whitelist()

async def _perm(e):
    u = str(e.user_id)
    try:
        return (
            u in Configurator.cm.get_cfg().others["ROOT_User"]
            or u in open("./Super_User.ini", "r").read().splitlines()
            or u in open("./Manage_User.ini", "r").read().splitlines()
        )
    except Exception:
        return False

def _fetch_kuaishou_data_sync(api_url, retries=3):
    """同步方式获取快手数据，带有重试机制"""
    for attempt in range(retries):
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200 and "data" in data:
                    return data
            if attempt < retries - 1:
                import time
                time.sleep(1)
        except Exception as e:
            if attempt < retries - 1:
                import time
                time.sleep(1)
            else:
                raise e
    return None

async def _fetch_kuaishou_data_async(api_url, retries=3):
    """异步方式获取快手数据，创建新的会话"""
    for attempt in range(retries):
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == 200 and "data" in data:
                            return data
            if attempt < retries - 1:
                await asyncio.sleep(1)
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(1)
            else:
                raise e
    return None

async def on_message(event, actions, Manager, Segments, Events, bot_name):
    if not hasattr(event, "message"):
        return False
        
    # 动态获取发送目标（支持群聊和私聊）
    send_kwargs = {"message": None}
    if hasattr(event, 'group_id'):
        send_kwargs["group_id"] = event.group_id
        is_group = True
    else:
        send_kwargs["user_id"] = event.user_id
        is_group = False
    
    m = str(event.message).strip()
    
    # 缓存配置减少重复获取
    cfg = Configurator.cm.get_cfg().others
    r = cfg.get('reminder', '')
    
    # 自动获取主人信息（从配置读取）
    root_users = cfg.get('ROOT_User', [])
    if root_users:
        owner_qq = root_users[0]
    else:
        owner_qq = '未设置主人'
    owner_name = cfg.get('kuaishou_plugin_owner_name', '主人')
    
    # 处理帮助命令
    if m == f"{r}快手解析帮助":
        if is_group:
            help_text = f"""快手解析插件帮助：
命令：
{r}本群解析加白 - 将本群加入白名单（停止解析）
{r}本群解析删白 - 将本群移出白名单（恢复解析）
{r}更新快手解析插件 - 更新插件（需要权限）

白名单功能：
- 在白名单内的群聊发送快手链接时，机器人不会解析
- 而是发送提示："本群为快手解析白名群，无法解析快手链接，若想开启快手解析功能，请联系{owner_name}({owner_qq})"

当前状态：
本群{'已加入' if str(event.group_id) in _whitelist else '未加入'}白名单"""
        else:
            help_text = f"""快手解析插件帮助（私聊模式）：
- 直接发送快手链接即可解析
- 无需白名单功能
- 支持获取视频信息、封面、视频链接等

{r}更新快手解析插件 - 更新插件（需要权限）"""
        
        send_kwargs["message"] = Manager.Message(Segments.Text(help_text))
        await actions.send(**send_kwargs)
        return True
    
    # 处理白名单命令（仅群聊）
    if is_group:
        if m == f"{r}本群解析加白":
            if not await _perm(event):
                send_kwargs["message"] = Manager.Message(Segments.Text("你没有权限执行此操作"))
                await actions.send(**send_kwargs)
                return True
                
            group_id = str(event.group_id)
            if group_id not in _whitelist:
                _whitelist.add(group_id)
                _save_whitelist()
                send_kwargs["message"] = Manager.Message(Segments.Text("已添加本群到快手解析白名单，将不再解析本群快手链接"))
                await actions.send(**send_kwargs)
            else:
                send_kwargs["message"] = Manager.Message(Segments.Text("本群已在快手解析白名单中"))
                await actions.send(**send_kwargs)
            return True
           
        elif m == f"{r}本群解析删白":
            if not await _perm(event):
                send_kwargs["message"] = Manager.Message(Segments.Text("你没有权限执行此操作"))
                await actions.send(**send_kwargs)
                return True
                
            group_id = str(event.group_id)
            if group_id in _whitelist:
                _whitelist.remove(group_id)
                _save_whitelist()
                send_kwargs["message"] = Manager.Message(Segments.Text("已从快手解析白名单中移除本群，将恢复解析本群快手链接"))
                await actions.send(**send_kwargs)
            else:
                send_kwargs["message"] = Manager.Message(Segments.Text("本群不在快手解析白名单中"))
                await actions.send(**send_kwargs)
            return True
    
    # 处理插件更新命令
    if m == f"{r}更新快手解析插件":
        if not await _perm(event):
            send_kwargs["message"] = Manager.Message(Segments.Text("你没有权限执行此操作"))
            await actions.send(**send_kwargs)
            return True
            
        try:
            # 这里可以设置更新插件的URL
            update_url = "https://raw.githubusercontent.com/wwwaaa123122/Jianer_Plugins_Index/refs/heads/main/KuaishouAnalysis/KuaishouAnalysis.py"  # 请替换为实际的更新URL
            save_path = __file__
            
            # 使用同步请求下载更新
            response = requests.get(update_url, timeout=30)
            if response.status == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                msg = f"快手解析插件已更新，请发送 {r}重载插件 完成重载！"
            else:
                msg = f"下载失败，状态码: {response.status_code}"
                
            send_kwargs["message"] = Manager.Message(Segments.Text(msg))
            await actions.send(**send_kwargs)
        except Exception as e:
            send_kwargs["message"] = Manager.Message(Segments.Text(f"更新失败: {e}"))
            await actions.send(**send_kwargs)
        return True

    # 检查当前群是否在白名单中（仅群聊）
    if is_group and str(event.group_id) in _whitelist:
        mat = _KUAISHOU_PATTERN.search(m)
        if mat:
            send_kwargs["message"] = Manager.Message(Segments.Text(
                f"本群为快手解析白名群，无法解析快手链接，若想开启快手解析功能，请联系{owner_name}({owner_qq})"
            ))
            await actions.send(**send_kwargs)
            return True
        return False

    # 正常解析流程
    mat = _KUAISHOU_PATTERN.search(m)
    if not mat:
        return False
        
    k_url = mat.group(1)
    api_url = f"http://api.corexwear.com/ks/ks.php?url={k_url}"
    
    try:
        # 尝试使用同步请求方式
        data = _fetch_kuaishou_data_sync(api_url, retries=3)
        
        if data is None:
            # 如果同步方式失败，尝试异步方式
            data = await _fetch_kuaishou_data_async(api_url, retries=3)
            
        if data is None:
            send_kwargs["message"] = Manager.Message(Segments.Text("快手解析失败: 所有重试尝试均失败"))
            await actions.send(**send_kwargs)
            return True
            
    except Exception as e:
        send_kwargs["message"] = Manager.Message(Segments.Text(f"快手解析失败: {str(e)}"))
        await actions.send(**send_kwargs)
        return True

    if data.get("code") != 200 or "data" not in data:
        send_kwargs["message"] = Manager.Message(Segments.Text(f"快手解析失败: {data.get('msg', '未知错误')}"))
        await actions.send(**send_kwargs)
        return True

    info = data["data"]
    music_info = data.get("music", {})
    
    # 群聊模式：使用合并转发
    # 私聊模式：直接发送文本和图片
    if is_group:
        # 1. 创建聊天记录格式的消息
        chat_nodes = []
        
        # 用户消息部分
        chat_nodes.append(
            Segments.CustomNode(
                str(event.user_id),
                getattr(event.sender, 'nickname', '用户'),
                Manager.Message([
                    Segments.Text(f"{m}")
                ])
            )
        )
        
        # 作者信息小节
        chat_nodes.append(
            Segments.CustomNode(
                str(event.self_id),
                bot_name,
                Manager.Message([
                    Segments.Image(info.get("avatar", "")),
                    Segments.Text(f"作者昵称：{info.get('author', '未知')}"),
                    Segments.Text(f"视频标题：{info.get('title', '无标题')}")
                ])
            )
        )
        
        # 视频信息小节
        chat_nodes.append(
            Segments.CustomNode(
                str(event.self_id),
                bot_name,
                Manager.Message([
                    Segments.Image(info.get("cover", "")),
                    Segments.Text("【视频信息】"),
                    Segments.Text(f"视频直链：{info.get('url', '无直链')}")
                ])
            )
        )
        
        # 音乐信息小节
        if music_info:
            chat_nodes.append(
                Segments.CustomNode(
                    str(event.self_id),
                    bot_name,
                    Manager.Message([
                        Segments.Text("【背景音乐】"),
                        Segments.Text(f"音乐名称：{music_info.get('musicName', '无信息')}"),
                        Segments.Text(f"音乐作者：{info.get('author', '未知')}")
                    ])
                )
            )
        
        # 发送聊天记录
        await actions.send_group_forward_msg(
            group_id=event.group_id,
            message=Manager.Message(*chat_nodes)
        )
    else:
        # 私聊模式：直接发送信息
        info_text = f"""【快手视频信息】
作者昵称：{info.get('author', '未知')}
视频标题：{info.get('title', '无标题')}"""
        
        if music_info:
            info_text += f"\n【背景音乐】\n音乐名称：{music_info.get('musicName', '无信息')}\n音乐作者：{info.get('author', '未知')}"
        
        info_text += f"\n\n视频直链：{info.get('url', '无直链')}"
        
        # 发送封面和信息
        send_kwargs["message"] = Manager.Message([
            Segments.Image(info.get("cover", "")),
            Segments.Text(info_text)
        ])
        await actions.send(**send_kwargs)
    
    # 发送视频
    video_url = info.get('url')
    if video_url:
        try:
            send_kwargs["message"] = Manager.Message([Segments.Video(video_url)])
            await actions.send(**send_kwargs)
        except Exception as e:
            send_kwargs["message"] = Manager.Message(Segments.Text(f"视频发送失败：{str(e)}"))
            await actions.send(**send_kwargs)
        
    return True

print("[星辰旅人QQ机器人]快手解析插件已加载")
