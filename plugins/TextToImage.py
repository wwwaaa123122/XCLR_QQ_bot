import aiohttp
import random
import base64
import asyncio
import re
import os

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "文生图"
HELP_MESSAGE = "#文生图 [提示词] —> 生成 AI 图片"

# Cloudflare AI 配置
CF_ACCOUNT_ID = "2228d557489e8da66c733ca71f6e5729"
CF_API_TOKEN = "_icVsni2kwZRZPBaxrM465QZav8XhGaHob7PMvSt"

LLM_MODEL = "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
CF_IMAGE_MODEL = "@cf/black-forest-labs/flux-1-schnell"

TMP_DIR = "/tmp"

RANDOM_PROMPTS = [
    "cyberpunk cat samurai graphic art, beautiful colors, cinematic lighting",
    "masterpiece, ultra-detailed anime girl in forest, sunlight, white dress",
    "frost glass, christmas theme, cute girl, aurora, snow, detailed light"
]

# Prompt 优化
async def refine_prompt(original_prompt, session):

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{LLM_MODEL}"

    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}"
    }

    system_prompt = (
        "You are a professional image prompt engineer. "
        "Translate user's input into English and expand it "
        "into a detailed AI image prompt. "
        "Output ONLY final prompt."
    )

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": original_prompt}
        ],
        "max_tokens": 800
    }

    try:
        async with session.post(url, headers=headers, json=payload, timeout=30) as resp:
            if resp.status == 200:
                result = await resp.json()
                raw = result.get("result", {}).get("response", "")

                cleaned = re.sub(
                    r'<think>.*?</think>',
                    '',
                    raw,
                    flags=re.DOTALL
                ).strip()

                cleaned = re.sub(
                    r'^(Here is.*?:|Prompt:)',
                    '',
                    cleaned,
                    flags=re.I
                ).strip()

                return cleaned if len(cleaned) > 5 else original_prompt

    except Exception as e:
        print("Prompt优化失败:", e)

    return original_prompt

# 生图
async def generate_image(prompt, session):

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_IMAGE_MODEL}"

    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt,
        "num_steps": 3,     
        "guidance": 3.0
    }

    async with session.post(url, headers=headers, json=payload, timeout=90) as resp:

        if resp.status != 200:
            text = await resp.text()
            raise Exception(f"API错误 {resp.status}: {text}")

        return await resp.read()

# 保存临时图片
def save_temp_image(image_bytes):

    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    file_path = os.path.join(
        TMP_DIR,
        f"ai_{random.randint(100000,999999)}.png"
    )

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return file_path

# 删除临时文件
async def cleanup_file(path):

    await asyncio.sleep(5)

    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

# 主监听
async def on_message(event, actions, Manager, Segments):

    msg = str(event.message).strip()

    if TRIGGHT_KEYWORD not in msg:
        return

    send_kwargs = {}

    if getattr(event, "group_id", None):
        send_kwargs["group_id"] = event.group_id
    else:
        send_kwargs["user_id"] = event.user_id

    parts = msg.split(TRIGGHT_KEYWORD, 1)

    raw_prompt = (
        parts[1].strip()
        if len(parts) > 1 and parts[1].strip()
        else random.choice(RANDOM_PROMPTS)
    )

    await actions.send(
        **send_kwargs,
        message=Manager.Message(
            Segments.Text("🧠 正在优化提示词...")
        )
    )

    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        optimized_prompt = await refine_prompt(
            raw_prompt,
            session
        )

        await actions.send(
            **send_kwargs,
            message=Manager.Message(
                Segments.Text("🎨 正在生成图片...")
            )
        )

        try:
            image_data = await generate_image(
                optimized_prompt,
                session
            )

            print(
                f"[TextToImage] 图片大小: {len(image_data)/1024:.2f} KB"
            )
            file_path = save_temp_image(image_data)

            await actions.send(
                **send_kwargs,
                message=Manager.Message(
                    Segments.Image(file_path)
                )
            )

            # 自动清理
            asyncio.create_task(
                cleanup_file(file_path)
            )

        except asyncio.TimeoutError:
            await actions.send(
                **send_kwargs,
                message=Manager.Message(
                    Segments.Text("⚠️ 生图超时")
                )
            )

        except Exception as e:
            await actions.send(
                **send_kwargs,
                message=Manager.Message(
                    Segments.Text(f"❌ 生成失败: {str(e)[:300]}")
                )
            )

    return True
