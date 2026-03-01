import base64 as _b, binascii as _ba, httpx as _h, re as _r
from Hyper import Configurator as _C

_K = "vxpinabo8u5i7"
_CI = "173022590d292f59740c0c01543113050c36370a35552340334e431212005723372a530357215c002238051f04215a4f147d281812203a1a3e391656"

def _d(ch, k):
    c = bytes.fromhex(ch)
    b = bytes([x ^ ord(k[i % len(k)]) for i, x in enumerate(c)])
    return _b.b64decode(b).decode("utf-8")

_API = _d(_CI, _K)
IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "Any"

async def _perm(e):
    u = str(e.user_id)
    try:
        return (
            u in _C.cm.get_cfg().others["ROOT_User"]
            or u in open("./Super_User.ini", "r").read().splitlines()
            or u in open("./Manage_User.ini", "r").read().splitlines()
        )
    except Exception:
        return False

async def on_message(event, actions, Manager, Segments):
    if not hasattr(event, "message"):
        return False
    
    # 动态获取发送目标（支持群聊和私聊）
    send_kwargs = {"message": None}
    if hasattr(event, 'group_id'):
        send_kwargs["group_id"] = event.group_id
    else:
        send_kwargs["user_id"] = event.user_id
    
    m = str(event.message).strip()
    r = _C.cm.get_cfg().others.get('reminder', '')
    if m == f"{r}更新抖音解析插件":
        if not await _perm(event):
            send_kwargs["message"] = Manager.Message(Segments.Text("你没有权限执行此操作"))
            await actions.send(**send_kwargs)
            return True
        try:
            url = "http://101.35.241.21:8888/down/V0uNtBcwT7zG.py"
            save_path = __file__
            async with _h.AsyncClient() as c:
                resp = await c.get(url, timeout=10.0)
                if resp.status_code == 200:
                    with open(save_path, "wb") as f:
                        f.write(resp.content)
                    send_kwargs["message"] = Manager.Message(Segments.Text(f"抖音解析插件已更新，请发送 {r}重载插件 完成重载！"))
                    await actions.send(**send_kwargs)
                else:
                    send_kwargs["message"] = Manager.Message(Segments.Text(f"下载失败，状态码: {resp.status_code}"))
                    await actions.send(**send_kwargs)
        except Exception as e:
            send_kwargs["message"] = Manager.Message(Segments.Text(f"更新失败: {e}"))
            await actions.send(**send_kwargs)
        return True

    mat = _r.search(r'(https?://v\.douyin\.com/[^\s]+)', m)
    if not mat:
        return False
    d_url = mat.group(1)
    api_url = _API.format(d_url)
    try:
        async with _h.AsyncClient() as c:
            resp = await c.get(api_url, timeout=10.0)
            data = resp.json()
    except Exception as e:
        send_kwargs["message"] = Manager.Message(Segments.Text(f"抖音解析失败: {e}"))
        await actions.send(**send_kwargs)
        return True

    if data.get("code") != 0 or "data" not in data:
        send_kwargs["message"] = Manager.Message(Segments.Text(f"抖音解析失败: {data.get('msg', '未知错误')}"))
        await actions.send(**send_kwargs)
        return True

    info = data["data"]
    a = info.get("author", {})
    author_msg = [
        Segments.Image(a.get("avatar", "")),
        Segments.Text(f"\n作者昵称：{a.get('name', '')}\n抖音号：{a.get('id', '')}\n签名：{a.get('signature', '')}")
    ]
    send_kwargs["message"] = Manager.Message(author_msg)
    await actions.send(**send_kwargs)

    msc = info.get("music", {})
    cnt = info.get("count", {})
    desc = info.get('desc', '')
    desc = _r.sub(r'[\r\n]+', ' ', desc)
    vurl = info.get('url', '')
    video_msg = [
        Segments.Image(info.get("cover", "")),
        Segments.Text(
            f"\n简介：{desc}\n"
            f"标签：{info.get('tag', '')}\n"
            f"音乐：{msc.get('title', '')}（作者：{msc.get('author', '')}，时长：{msc.get('duration', '')}秒）\n"
            f"👍点赞：{cnt.get('like', 0)}  💬评论：{cnt.get('comment', 0)}  📢分享：{cnt.get('share', 0)}  ⭐收藏：{cnt.get('collect', 0)}\n"
            f"🔗视频直链：{vurl}"
        )
    ]
    await actions.send(
        group_id=event.group_id,
        message=Manager.Message(video_msg)
    )

    if vurl:
        try:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message([Segments.Video(vurl)])
            )
        except Exception as e:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text(f"视频发送失败：{e}"))
            )
    return True

print("[Xiaoyi_QQ]抖音解析插件已加载")