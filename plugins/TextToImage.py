import aiohttp
import random
import base64
import asyncio
import re
import tempfile
import os

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "文生图"
HELP_MESSAGE = "#文生图 [提示词] —> 生成 AI 图片"

# Cloudflare AI API 配置
CF_ACCOUNT_ID = "2228d557489e8da66c733ca71f6e5729" 
CF_API_TOKEN = "_icVsni2kwZRZPBaxrM465QZav8XhGaHob7PMvSt"    
LLM_MODEL = "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
CF_IMAGE_MODEL = "@cf/black-forest-labs/flux-1-schnell"

# 注意：Imgur 匿名上传有频率限制（每小时约50张）
# 如果频繁使用，建议注册账号获取自己的 Client ID
# 注册地址：https://api.imgur.com/oauth2/addclient

RANDOM_PROMPTS = [
    "cyberpunk cat samurai graphic art, beautiful colors, cinematic lighting",
    "masterpiece, ultra-detailed anime girl in forest, sunlight, white dress",
    "frost glass, christmas theme, cute girl, aurora, snow, detailed light"
]

async def refine_prompt(original_prompt, session):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{LLM_MODEL}"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    
    system_prompt = "You are a professional image prompt engineer. Task: Translate the user's input into English and expand it into a detailed prompt for AI generation. Rule: Output ONLY the final English prompt. No conversation, no 'Here is your prompt', no intro."

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": original_prompt}
        ],
        "max_tokens": 1000
    }

    try:
        async with session.post(url, headers=headers, json=payload, timeout=30) as resp:
            if resp.status == 200:
                result = await resp.json()
                raw_text = result.get("result", {}).get("response", "")
                #去除think标签
                cleaned = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
                
                if "<think>" in cleaned:
                    cleaned = cleaned.split("<think>")[0].strip()
                
                cleaned = re.sub(r'^(Here is the refined prompt:|Prompt:)', '', cleaned, flags=re.IGNORECASE).strip()
                
                return cleaned if len(cleaned) > 5 else original_prompt
            else:
                return original_prompt
    except Exception as e:
        print(f"润色出错: {e}")
        return original_prompt

async def generate_image(prompt, session):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_IMAGE_MODEL}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "num_steps": 4,
        "guidance": 3.5,
    }
    
    try:
        async with session.post(url, headers=headers, json=payload, timeout=90) as resp:
            if resp.status == 200:
                image_data = await resp.read()
                return image_data
            else:
                error_text = await resp.text()
                raise Exception(f"API 返回错误: {resp.status} - {error_text}")
    except asyncio.TimeoutError:
        raise Exception("生图请求超时")
    except Exception as e:
        raise Exception(f"生图请求失败: {e}")

async def upload_to_imgur(image_data, session):
    """上传图片到 Imgur（备用方案）"""
    try:
        # 注意：需要注册 Imgur 账号获取 client ID
        # 这里使用匿名上传
        headers = {"Authorization": "Client-ID 546c25a59c58ad7"}  # 公共 Client ID
        
        async with session.post(
            "https://api.imgur.com/3/image",
            headers=headers,
            data={"image": base64.b64encode(image_data), "type": "base64"},
            timeout=30
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                if result.get("success"):
                    return result["data"]["link"]
    except Exception as e:
        print(f"Imgur 上传失败: {e}")
    return None

async def on_message(event, actions, Manager, Segments):
    msg = str(event.message).strip()
    if TRIGGHT_KEYWORD not in msg:
        return 

    # 动态获取发送目标（支持群聊和私聊）
    send_kwargs = {"message": None}
    if getattr(event, 'group_id', None):
        send_kwargs["group_id"] = event.group_id
    else:
        send_kwargs["user_id"] = event.user_id

    parts = msg.split(TRIGGHT_KEYWORD, 1)
    raw_prompt = parts[1].strip() if len(parts) > 1 and parts[1].strip() else random.choice(RANDOM_PROMPTS)

    send_kwargs["message"] = Manager.Message(Segments.Text(f"正在智能优化提示词... 🧠"))
    await actions.send(**send_kwargs)

    timeout = aiohttp.ClientTimeout(total=90)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        optimized_prompt = await refine_prompt(raw_prompt, session)
        
        send_kwargs["message"] = Manager.Message(Segments.Text(f"正在生成图片... 🎨"))
        await actions.send(**send_kwargs)

        try:
            image_data = await generate_image(optimized_prompt, session)
            
            # 调试信息：检查图片数据
            print(f"[TextToImage] 图片数据大小: {len(image_data)} bytes")
            
            # 验证 PNG 格式（检查文件头）
            if len(image_data) < 8 or not image_data.startswith(b'\x89PNG'):
                print(f"[TextToImage] 警告：图片数据可能不是有效的 PNG 格式")
                print(f"[TextToImage] 文件头: {image_data[:8].hex() if image_data else '空数据'}")
            else:
                print(f"[TextToImage] 图片格式验证通过: PNG")
            
            # 方案1：尝试上传到 Imgur 并使用 URL 发送（最稳定）
            print(f"[TextToImage] 尝试上传到 Imgur...")
            image_url = await upload_to_imgur(image_data, session)
            
            if image_url:
                print(f"[TextToImage] Imgur 上传成功: {image_url}")
                send_kwargs["message"] = Manager.Message(Segments.Image(image_url))
                await actions.send(**send_kwargs)
                print(f"[TextToImage] URL 发送成功")
            else:
                # 方案2：如果上传失败，使用 base64
                print(f"[TextToImage] Imgur 上传失败，改用 base64 发送...")
                import base64
                b64_data = base64.b64encode(image_data).decode('utf-8')
                
                print(f"[TextToImage] Base64 长度: {len(b64_data)} 字符")
                
                try:
                    image_url = f"base64://{b64_data}"
                    print(f"[TextToImage] 尝试 base64 发送: {image_url[:50]}...")
                    
                    send_kwargs["message"] = Manager.Message(Segments.Image(image_url))
                    await actions.send(**send_kwargs)
                    print(f"[TextToImage] base64 发送成功")
                    
                except Exception as e:
                    print(f"[TextToImage] base64 发送失败: {e}")
                    # 方案3：最后备选，使用 file 协议
                    print(f"[TextToImage] 尝试 file 协议发送...")
                    
                    temp_dir = "temp"
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    
                    filename = f"texttoimage_{event.user_id}_{asyncio.get_event_loop().time()}.png"
                    filepath = os.path.join(temp_dir, filename)
                    
                    with open(filepath, "wb") as f:
                        f.write(image_data)
                    
                    print(f"[TextToImage] 图片已保存到: {filepath}")
                    send_kwargs["message"] = Manager.Message(Segments.Image(f"file:///{os.path.abspath(filepath)}"))
                    await actions.send(**send_kwargs)
                    print(f"[TextToImage] file 协议发送成功")
            
        except asyncio.TimeoutError:
            send_kwargs["message"] = Manager.Message(Segments.Text("⚠️ 生图请求超时，请重试。"))
            await actions.send(**send_kwargs)
        except Exception as e:
            send_kwargs["message"] = Manager.Message(Segments.Text(f"❌ 生成失败：{str(e)[:500]}"))
            await actions.send(**send_kwargs)

    return True
