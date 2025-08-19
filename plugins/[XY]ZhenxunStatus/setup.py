import os
import asyncio
import json
from datetime import datetime
import jinja2
from playwright.async_api import async_playwright
from Hyper import Configurator
import platform
import psutil
import sys

# ================= 配置文件安全加载 =================
def safe_load_config():
    config_file = "config.json"
    default_config = {
        "uin": "3655437054",
        "owner": ["3385016019"],
        "others": {
            "bot_name": "星辰旅人",
            "reminder": "星辰旅人"
        }
    }
    
    # 1. 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"[警告] 配置文件 {config_file} 不存在，创建默认配置")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config
    
    # 2. 检查文件是否为空
    if os.path.getsize(config_file) == 0:
        print(f"[警告] 配置文件 {config_file} 为空，恢复默认配置")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config
    
    # 3. 安全加载配置文件
    try:
        config_loader = Configurator.Config(file=config_file)
        return config_loader.load_from_file()
    except Exception as e:
        print(f"[严重] 配置文件加载失败: {e}, 使用默认配置")
        return default_config

# 初始化配置管理器
try:
    config_data = safe_load_config()
    Configurator.cm = Configurator.ConfigManager(config_data)
except Exception as e:
    print(f"[致命] 配置管理器初始化失败: {e}")
    # 尝试创建更简单的配置作为最后手段
    Configurator.cm = Configurator.ConfigManager({
        "uin": "000000",
        "owner": ["100000000"],
        "others": {"bot_name": "Bot", "reminder": "状态"}
    })

TRIGGHT_KEYWORD = "Any"
RES_DIR = os.path.join(os.path.dirname(__file__), "res")

# 确保资源目录存在
os.makedirs(RES_DIR, exist_ok=True)

# ================= 工具函数优化 =================
def format_cpu_freq(val):
    """更健壮的CPU频率格式化"""
    try:
        val = float(val)
        if val >= 10**9:  # GHz范围
            return f"{val/10**9:.2f} GHz"
        elif val >= 10**6:  # MHz范围
            return f"{val/10**6:.2f} MHz"
        return f"{val:.0f} Hz"
    except (TypeError, ValueError):
        return "N/A"

def auto_convert_unit(val):
    """带单位的自动���换，处理更多数据类型"""
    if isinstance(val, (int, float)):
        units = ["B", "KB", "MB", "GB", "TB"]
        idx = 0
        val = float(val)
        while val >= 1024 and idx < len(units) - 1:
            val /= 1024
            idx += 1
        return f"{val:.2f} {units[idx]}" if idx > 0 else f"{int(val)} {units[idx]}"
    return str(val)

# ================= 资源处理优化 =================
def get_css_content():
    """安全获取CSS内容，提供备用样式"""
    css_path = os.path.join(RES_DIR, "index.css")
    if not os.path.exists(css_path):
        return """
        body { font-family: sans-serif; }
        .wrapper { padding: 20px; background: #f0f0f0; }
        """
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def get_local_image(filename):
    """更安全的本地图片路径处理"""
    path = os.path.join(RES_DIR, filename)
    return path if os.path.exists(path) else None

# ================= 主要功能优化 =================
async def render_status_image(status_data: dict, config) -> str:
    """生成状态图片，增加错误处理和资源检查"""
    # 1. 模板处理
    template_path = os.path.join(RES_DIR, "index.html.jinja")
    if not os.path.exists(template_path):
        print(f"[错误] 模板文件不存在: {template_path}")
        return None
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except Exception as e:
        print(f"[错误] 模板读取失败: {e}")
        return None
    
    # 2. CSS处理
    css_content = get_css_content()
    template_content = template_content.replace(
        '<link rel="stylesheet" href="/res/index.css" />',
        f'<style>{css_content}</style>'
    )
    
    # 3. 图片资源检查
    top_image = get_local_image("top.jpg") or get_local_image("default_top.jpg")
    bg_image = get_local_image("bk.png") or get_local_image("default_bg.png")
    
    # 4. 模板渲染
    env = jinja2.Environment()
    env.filters["format_cpu_freq"] = format_cpu_freq
    env.filters["auto_convert_unit"] = auto_convert_unit
    
    try:
        template = env.from_string(template_content)
        owner_list = config.owner if hasattr(config, 'owner') else []
        owner_qq = str(owner_list[0]) if owner_list else "0"
        
        html_content = template.render(
            d=status_data,
            config=config,
            css_content=css_content,
            top_image_path=top_image,
            abs_image_path=bg_image,
            bot_avatar_path=f"http://q2.qlogo.cn/headimg_dl?dst_uin={owner_qq}&spec=640",
        )
    except Exception as e:
        print(f"[错误] 模板渲染失败: {e}")
        return None
    
    # 5. 截图处理
    img_name = f"status_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    img_path = os.path.join(RES_DIR, img_name)
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 900, "height": 600})
            await page.set_content(html_content)
            await asyncio.sleep(0.5)  # 增加等待时间确保渲染完成
            
            elem = await page.query_selector("div.wrapper")
            if elem:
                await elem.screenshot(path=img_path)
            else:
                await page.screenshot(path=img_path, full_page=True)
            await browser.close()
        return img_path
    except Exception as e:
        print(f"[错误] 截图生成失败: {e}")
        return None

async def collect_status():
    """收集系统状态信息，增加异常处理"""
    try:
        cfg = Configurator.cm.get_cfg()
        others = getattr(cfg, "others", {})
        now = datetime.now()

        # CPU信息
        cpu_freq = 0
        try:
            cpu_freq = psutil.cpu_freq().current
        except Exception:
            pass
            
        cpu_brand = platform.processor() or "未知CPU"
        if not cpu_brand or cpu_brand == "":
            cpu_brand = platform.machine() or "未知架构"

        # 内存信息
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        memory_stat = {
            "percent": mem.percent,
            "used": mem.used,
            "total": mem.total,
        }
        swap_stat = {
            "percent": swap.percent,
            "used": swap.used,
            "total": swap.total,
        }

        # 磁盘信息
        disk_usage = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disk_usage.append({
                    "name": part.device,
                    "mount": part.mountpoint,
                    "percent": usage.percent,
                    "used": usage.used,
                    "total": usage.total,
                    "exception": False,
                })
            except Exception as e:
                disk_usage.append({
                    "name": part.device,
                    "mount": part.mountpoint,
                    "percent": 0,
                    "used": 0,
                    "total": 0,
                    "exception": True,
                })

        # 插件计数
        plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))
        plugin_count = 0
        if os.path.isdir(plugins_dir):
            for root, dirs, files in os.walk(plugins_dir):
                # 排除缓存目录
                if "__pycache__" in root:
                    continue
                # 统计Python文件
                plugin_count += sum(1 for f in files if f.endswith('.py') and not f.startswith('_'))
                # 统计有效插件目录
                plugin_count += sum(1 for d in dirs if not d.startswith('_') and not d == "__pycache__")

        return {
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "system_name": platform.platform(),
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": cpu_freq,
            "cpu_brand": cpu_brand,
            "memory_stat": memory_stat,
            "swap_stat": swap_stat,
            "disk_usage": disk_usage,
            "python_version": sys.version.split()[0],
            "plugin_count": plugin_count,
            "bot_name": others.get("bot_name", "未知机器人"),
            "ps_version": "1.0.0",
            "template_version": "XiaoyiDev",
        }
    except Exception as e:
        print(f"[状态收集] 错误: {e}")
        return {
            "error": f"状态收集失败: {str(e)}"
        }

# ================= 消息处理优化 =================
async def on_message(event, actions, Manager, Segments):
    if not hasattr(event, "message"):
        return False
        
    msg = str(event.message).strip()
    reminder = getattr(getattr(Configurator.cm.get_cfg(), "others", {}).get("reminder", "")
    trigger_words = ["status", f"{reminder}状态", "状态", "系统状态"]
    
    if msg not in trigger_words:
        return False

    try:
        cfg = Configurator.cm.get_cfg()
        status_data = await collect_status()
        
        if "error" in status_data:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text(status_data["error"]))
            return True
            
        img_path = await render_status_image(cfg)
        
        if not img_path:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text("状态图片生成失败，请检查日志")))
            return True
            
        await actions.send(
            group_id=event.group_id,
            message=Manager.Message([
                Segments.Image(f"file:///{img_path}")
            ])
        )
        
        # 延迟删除避免发送前被删除
        await asyncio.sleep(10)
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
        except Exception as e:
            print(f"[清理] 临时图片删除失败: {e}")
            
        return True
    except Exception as e:
        print(f"[消息处理] 错误: {e}")
        await actions.send(
            group_id=event.group_id,
            message=Manager.Message(Segments.Text(f"状态请求处理失败: {e}")))
        return True

print("[状态插件] 真寻状态插件已安全加载")
