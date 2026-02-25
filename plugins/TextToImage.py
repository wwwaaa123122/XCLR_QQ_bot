import aiohttp
import random
import base64
import asyncio
import re
import os

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "文生图"
HELP_MESSAGE = "#文生图 [提示词] —> 生成 AI 图片"

# Cloudflare AI API 配置
CF_ACCOUNT_ID = "2228d557489e8da66c733ca71f6e5729" 
CF_API_TOKEN = "_icVsni2kwZRZPBaxrM465QZav8XhGaHob7PMvSt"    
LLM_MODEL = "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
CF_IMAGE_MODEL = "@cf/black-forest-labs/flux-1-schnell"

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
            
            print(f"[TextToImage] 图片数据大小: {len(image_data)} bytes")
            
            b64_data = base64.b64encode(image_data).decode('utf-8')
            image_url = f"base64://{b64_data}"
            
            send_kwargs["message"] = Manager.Message(Segments.Image(image_url))
            await actions.send(**send_kwargs)
            
        except asyncio.TimeoutError:
            send_kwargs["message"] = Manager.Message(Segments.Text("⚠️ 生图请求超时，请重试。"))
            await actions.send(**send_kwargs)
        except Exception as e:
            send_kwargs["message"] = Manager.Message(Segments.Text(f"❌ 生成失败：{str(e)[:500]}"))
            await actions.send(**send_kwargs)

    return True
