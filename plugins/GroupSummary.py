from Hyper import Configurator, Manager, Segments
import os, json, asyncio, base64, functools, traceback, re
from datetime import datetime, timedelta

# --- 框架必须的触发标识符 ---
TRIGGHT_KEYWORD = "Any"
HELP_MESSAGE = "#群总结 -> 生成今日聊天总结图片"

# 配置与路径初始化
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())
CACHE_DIR = os.path.join("temp", "group_summary_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

try:
    import imgkit
except ImportError:
    imgkit = None

_group_summary_scheduler_started = False

# --- 1. 缓存逻辑 (增加格式兼容性) ---
async def append_message_to_cache(event, actions):
    if not hasattr(event, 'group_id'): return
    today = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(CACHE_DIR, f"{event.group_id}_{today}.json")

    sender = str(event.user_id)
    try:
        member = await actions.get_group_member_info(event.group_id, event.user_id)
        raw = getattr(member.data, 'raw', {})
        sender = raw.get('card') or raw.get('nickname') or sender
    except: pass

    entry = {"n": sender, "c": str(event.message), "t": datetime.now().strftime("%H:%M")}

    arr = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try: arr = json.load(f)
            except: arr = []

    arr.append(entry)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(arr[-3000:], f, ensure_ascii=False)

# --- 2. 渲染逻辑 (解决排版压缩问题) ---
async def render_summary_image(summary_text, group_id):
    if not imgkit: return "未安装 imgkit", None

    # 清理 Markdown 标签以免影响视觉效果
    clean_text = summary_text.replace("**", "").replace("###", "").strip()

    font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets/sz.ttf"))
    font_css = ""
    if os.path.exists(font_path):
        with open(font_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            font_css = f"@font-face {{font-family:'Custom';src:url(data:font/ttf;base64,{b64});}} body{{font-family:'Custom',sans-serif!important;}}"

    # 优化后的 HTML 模板：解决宽度压缩和字体溢出，文本居中
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>
        {font_css}
        * {{ box-sizing: border-box; }}
        body {{ 
            background: #0f172a; margin: 0 auto; padding: 20px 0; 
            width: 700px; color: #e6edf3; font-family: sans-serif; 
        }}
        .card {{ 
            background: #1e293b; border-radius: 16px; padding: 40px; width: 660px; margin: 0 auto; 
            border: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        h1 {{ 
            color: #38bdf8; text-align: center; margin: 0 0 25px 0; 
            font-size: 28px; border-bottom: 2px solid #334155; padding-bottom: 20px;
        }}
        .content {{ 
            white-space: pre-wrap; word-wrap: break-word; 
            line-height: 1.8; font-size: 18px; color: #f1f5f9; 
            text-align: center;  /* 添加文本居中 */
            margin: 0 auto;
            max-width: 580px;  /* 限制最大宽度，使文本更易阅读 */
        }}
        .footer {{ 
            text-align: center; margin-top: 30px; font-size: 14px; 
            color: #64748b; border-top: 1px solid #334155; padding-top: 20px;
        }}
        .content p {{ 
            margin: 15px 0; text-align: center;
        }}
        .content ul, .content ol {{
            text-align: left;  /* 列表保持左对齐 */
            display: inline-block;  /* 使列表在居中容器内左对齐 */
            margin: 15px auto;
            padding-left: 20px;
        }}
    </style></head><body><div class="card">
        <h1>📊 群聊每日总结</h1>
        <div class="content">{clean_text}</div>
        <div class="footer">群号: {group_id} | {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div></body></html>
    """

    out_path = os.path.abspath(os.path.join(CACHE_DIR, f"out_{group_id}.jpg"))
    opts = {
        'format': 'jpg', 'encoding': "UTF-8", 'quiet': '', 
        'enable-local-file-access': '', 'disable-smart-width': '', 'zoom': '1.2'
    }

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, functools.partial(imgkit.from_string, html, out_path, options=opts))
        return None, out_path
    except Exception as e:
        return f"图片渲染出错: {e}", None

# --- 3. 业务逻辑 (修复 't' 键缺失的兼容性) ---
async def do_summarize(group_id, actions, days=1):
    msgs = []
    for i in range(days):
        dt = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        p = os.path.join(CACHE_DIR, f"{group_id}_{dt}.json")
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                try: msgs.extend(json.load(f))
                except: continue

    if not msgs: return "暂无聊天记录缓存"

    try:
        from Tools.deepseek import dsr114
        cfg = Configurator.cm.get_cfg().others

        # 兼容性读取：处理 n/sender_name, c/content, t/timestamp
        lines = []
        for m in msgs[-1000:]:
            time_str = m.get('t') or m.get('timestamp', '00:00')
            if len(time_str) > 10: time_str = time_str[11:16]
            name = m.get('n') or m.get('sender_name', 'Unknown')
            content = m.get('c') or m.get('content', '')
            lines.append(f"[{time_str}] {name}: {content}")

        prompt = "你是一个群聊记录总结助手。请根据提供的消息生成摘要。要求：1. 核心话题；2. 活跃成员；3. 幽默评价。条理清晰，300字内。"
        ds = dsr114(prompt, "\n".join(lines), {}, group_id, 'deepseek-chat', cfg.get('bot_name','Bot'), cfg.get('deepseek_key'))
        res = "".join([str(p) for p, k in ds.Response() if k == 'message'])
        if not res: return "AI 未返回内容"
    except Exception as e:
        return f"AI 故障: {e}"

    err, img = await render_summary_image(res, group_id)
    if err: return err

    await actions.send(group_id=int(group_id), message=Manager.Message([Segments.Image(f"file:///{img}")]))
    if os.path.exists(img): os.remove(img)
    return None

# --- 4. 定时与入口 ---
async def scheduler(actions):
    global _group_summary_scheduler_started
    while _group_summary_scheduler_started:
        now = datetime.now()
        target = now.replace(hour=21, minute=41, second=0, microsecond=0)
        if now >= target: target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

        for f in os.listdir(CACHE_DIR):
            if f.endswith(f"_{datetime.now().strftime('%Y-%m-%d')}.json"):
                await do_summarize(f.split('_')[0], actions)
                await asyncio.sleep(5)

async def on_message(event, actions, Events, Manager, Segments):
    global _group_summary_scheduler_started
    if not isinstance(event, Events.GroupMessageEvent): return False

    asyncio.create_task(append_message_to_cache(event, actions))

    if not _group_summary_scheduler_started:
        _group_summary_scheduler_started = True
        asyncio.create_task(scheduler(actions))

    content = str(event.message).strip()
    prefix = Configurator.cm.get_cfg().others.get('reminder', '#')

    if content.startswith(f"{prefix}群总结"):
        days = 1
        if " " in content:
            try: days = min(7, max(1, int(content.split()[1])))
            except: pass
        await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text("⏳ 正在分析聊记录...")))
        err = await do_summarize(str(event.group_id), actions, days)
        if err: await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text(f"❌ {err}")))
        return True
    return False
