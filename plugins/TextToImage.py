import aiohttp
import random
import base64
import asyncio
import re

# === 配置区域 ===
TRIGGHT_KEYWORD = "文生图"
HELP_MESSAGE = "#文生图 [提示词] —> 生成 AI 图片"

# 1. Cloudflare Worker 生图接口配置
WORKER_URL = "https://ai.mcxclr.top"
PASSWORD = "aaawww123122"

# 2. Cloudflare Workers AI 润色配置 (DeepSeek)
CF_ACCOUNT_ID = "2228d557489e8da66c733ca71f6e5729" 
CF_API_TOKEN = "_icVsni2kwZRZPBaxrM465QZav8XhGaHob7PMvSt"    
LLM_MODEL = "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"

# 3. 随机提示词备用
RANDOM_PROMPTS = [
    "cyberpunk cat samurai graphic art, beautiful colors, cinematic lighting",
    "masterpiece, ultra-detailed anime girl in forest, sunlight, white dress",
    "frost glass, christmas theme, cute girl, aurora, snow, detailed light"
]

async def refine_prompt(original_prompt, session):
    """
    使用 DeepSeek 模型进行翻译和润色，并严格清洗思考过程
    """
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{LLM_MODEL}"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    
    system_prompt = (
        "You are a professional image prompt engineer. "
        "Task: Translate the user's input into English and expand it into a detailed prompt for AI generation. "
        "Rule: Output ONLY the final English prompt. No conversation, no 'Here is your prompt', no intro."
    )

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": original_prompt}
        ],
        "max_tokens": 1000 # 给予足够空间防止思考过程过长导致截断
    }

    try:
        async with session.post(url, headers=headers, json=payload, timeout=30) as resp:
            if resp.status == 200:
                result = await resp.json()
                raw_text = result.get("result", {}).get("response", "")
                
                # --- 强力清洗逻辑 ---
                # 1. 处理完整的 <think>...</think>
                cleaned = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
                
                # 2. 处理被截断的 <think> (没有闭合标签的情况)
                if "<think>" in cleaned:
                    # 如果还存在 <think>，说明标签没闭合，截断它之后的所有内容
                    cleaned = cleaned.split("<think>")[0].strip()
                
                # 3. 处理模型可能残留的引导语
                cleaned = re.sub(r'^(Here is the refined prompt:|Prompt:)', '', cleaned, flags=re.IGNORECASE).strip()
                
                # 如果清洗后内容太短，说明润色失败，返回原词
                return cleaned if len(cleaned) > 5 else original_prompt
            else:
                return original_prompt
    except Exception as e:
        print(f"润色出错: {e}")
        return original_prompt

async def on_message(event, actions, Manager, Segments):
    """
    当用户发送触发词时调用。
    """
    msg = str(event.message).strip()
    if TRIGGHT_KEYWORD not in msg:
        return 

    # 提取提示词
    parts = msg.split(TRIGGHT_KEYWORD, 1)
    raw_prompt = parts[1].strip() if len(parts) > 1 and parts[1].strip() else random.choice(RANDOM_PROMPTS)

    # 发送初步反馈
    await actions.send(
        group_id=event.group_id,
        message=Manager.Message(Segments.Text(f"正在智能优化提示词... 🧠"))
    )

    timeout = aiohttp.ClientTimeout(total=90)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # 1. 调用 DeepSeek 润色
        optimized_prompt = await refine_prompt(raw_prompt, session)

        # 2. 告知用户优化结果并开始生图
        await actions.send(
            group_id=event.group_id,
            message=Manager.Message(Segments.Text(f"优化完成，正在绘制中... 🪄\n\n【最终词】：{optimized_prompt}"))
        )

        try:
            # 3. 调用生图 Worker API
            async with session.post(
                f"{WORKER_URL}/api",
                json={
                    "prompt": optimized_prompt,
                    "model": "flux-1-schnell",
                    "password": PASSWORD
                }
            ) as resp:
                content_type = resp.headers.get("content-type", "")
                body = await resp.read()

                if resp.status == 200 and "image" in content_type:
                    # 图片转 base64
                    b64 = base64.b64encode(body).decode("ascii")
                    await actions.send(
                        group_id=event.group_id,
                        message=Manager.Message(Segments.Image(f"base64://{b64}"))
                    )
                else:
                    err_text = body.decode("utf-8") if body else "Unknown Error"
                    await actions.send(
                        group_id=event.group_id,
                        message=Manager.Message(Segments.Text(f"❌ 生成失败：\n{err_text[:500]}"))
                    )

        except asyncio.TimeoutError:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text("⚠️ 生图请求超时，请重试。"))
            )
        except Exception as e:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text(f"⚠️ 系统错误：{e}"))
            )

    return True  # 阻断后续功能