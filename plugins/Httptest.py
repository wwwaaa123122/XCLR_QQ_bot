import aiohttp
import asyncio
from urllib.parse import urlparse
from Hyper import Configurator

# 从配置中获取提醒前缀
try:
    Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())
    reminder = Configurator.cm.get_cfg().others["reminder"]
except:
    reminder = "/"  # 默认值，如果无法读取配置

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "http"
HELP_MESSAGE = f"{reminder}http [网址] -> 检查网址的HTTP状态码"

async def on_message(event, actions, Manager, Segments):
    # 提取用户消息中的网址
    user_message = str(event.message).strip()

    # 移除reminder前缀（如果有）
    if user_message.startswith(reminder):
        command = user_message[len(reminder):].strip()
    else:
        command = user_message.strip()

    # 检查是否是HTTP状态命令
    if not command.startswith("http"):
        return False  # 不是HTTP状态命令，不处理
    
    # 动态获取发送目标（支持群聊和私聊）
    send_kwargs = {}
    if getattr(event, 'group_id', None):
        send_kwargs["group_id"] = event.group_id
    else:
        send_kwargs["user_id"] = event.user_id
    
    # 提取网址部分
    parts = command.split()
    
    if len(parts) < 2:
        # 如果没有提供网址，发送使用说明
        send_kwargs["message"] = Manager.Message(
            Segments.Text(f"请提供要检查的网址，例如：http https://example.com")
        )
        await actions.send(**send_kwargs)
        return True
    
    url = parts[1]
    # 确保URL有协议前缀
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # 验证URL格式
    try:
        parsed_url = urlparse(url)
        if not parsed_url.netloc:  # 如果没有域名部分
            raise ValueError("无效的URL")
    except:
        send_kwargs["message"] = Manager.Message(
            Segments.Text("提供的网址格式无效，请检查后重试")
        )
        await actions.send(**send_kwargs)
        return True
    
    # 发送等待消息
    send_kwargs["message"] = Manager.Message(
        Segments.Text(f"正在检查 {url} 的状态码...")
    )
    await actions.send(**send_kwargs)
    
    try:
        # 设置超时时间
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 发送HEAD请求（更高效，只获取头部信息）
            async with session.head(url, allow_redirects=True) as response:
                status_code = response.status
                status_message = f"HTTP状态码: {status_code}"
                
                # 添加状态码含义说明
                status_categories = {
                    100: "信息响应",
                    200: "成功",
                    300: "重定向",
                    400: "客户端错误",
                    500: "服务器错误"
                }
                
                category = status_code // 100
                category_name = status_categories.get(category, "未知")
                
                # 常见状态码的详细说明
                common_status_codes = {
                    200: "OK - 请求成功",
                    301: "Moved Permanently - 永久重定向",
                    302: "Found - 临时重定向",
                    304: "Not Modified - 未修改",
                    400: "Bad Request - 错误请求",
                    401: "Unauthorized - 未授权",
                    403: "Forbidden - 禁止访问",
                    404: "Not Found - 未找到",
                    500: "Internal Server Error - 服务器内部错误",
                    502: "Bad Gateway - 错误网关",
                    503: "Service Unavailable - 服务不可用",
                    504: "Gateway Timeout - 网关超时"
                }
                
                detail = common_status_codes.get(status_code, f"{category_name}响应")
                
                # 获取重定向信息（如果有）
                redirect_info = ""
                if response.history:
                    redirects = [f"{r.status} {r.url}" for r in response.history]
                    redirect_info = f"\n重定向路径: {' -> '.join(redirects)}"
                
                # 发送结果
                result_message = f"{status_message}\n含义: {detail}{redirect_info}"
                
                send_kwargs["message"] = Manager.Message(Segments.Text(result_message))
                await actions.send(**send_kwargs)
    
    except asyncio.TimeoutError:
        error_msg = f"请求超时：无法在10秒内连接到 {url}"
        send_kwargs["message"] = Manager.Message(Segments.Text(error_msg))
        await actions.send(**send_kwargs)
    except aiohttp.ClientConnectorError:
        error_msg = f"连接错误：无法连接到 {url}，可能是域名解析失败或服务器不可达"
        send_kwargs["message"] = Manager.Message(Segments.Text(error_msg))
        await actions.send(**send_kwargs)
    except aiohttp.ClientError as e:
        error_msg = f"请求失败：{str(e)}"
        send_kwargs["message"] = Manager.Message(Segments.Text(error_msg))
        await actions.send(**send_kwargs)
    except Exception as e:
        error_msg = f"发生未知错误：{str(e)}"
        send_kwargs["message"] = Manager.Message(Segments.Text(error_msg))
        await actions.send(**send_kwargs)
    
    return True