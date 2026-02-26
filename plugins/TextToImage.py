import aiohttp
import random
import asyncio
import re
import os
import io
from PIL import Image

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "文生图"
HELP_MESSAGE = "#文生图 [提示词] -> 生成 AI 图片"

# Cloudflare AI 配置
CF_ACCOUNT_ID = "2228d557489e8da66c733ca71f6e5729"
CF_API_TOKEN = "_icVsni2kwZRZPBaxrM465QZav8XhGaHob7PMvSt"

LLM_MODEL = "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
CF_IMAGE_MODEL = "@cf/black-forest-labs/flux-1-schnell"

TMP_DIR = "/tmp/napcat_ai_img"
os.makedirs(TMP_DIR, exist_ok=True)

RANDOM_PROMPTS = [
    "cyberpunk cat samurai, cinematic lighting",
    "anime girl in forest, sunlight, masterpiece",
    "aurora sky, winter theme, detailed light"
]

# Prompt 优化
async def refine_prompt(original_prompt, session):

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{LLM_MODEL}"

    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}"
    }

    payload = {
        "messages": [
            {"role": "system", "content":
             "Translate and expand user prompt into detailed English AI image prompt. Output prompt only."},
            {"role": "user", "content": original_prompt}
        ]
    }

    try:
        async with session.post(url, headers=headers, json=payload, timeout=30) as resp:
            if resp.status == 200:
                result = await resp.json()
                text = result.get("result", {}).get("response", "")

                text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
                text = re.sub(r'^(Prompt:|Here.*?:)', '', text, flags=re.I)

                text = text.strip()
                if len(text) > 5:
                    return text
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
        "num_steps": 4,
        "guidance": 2.5
    }

    async with session.post(url, headers=headers, json=payload, timeout=90) as resp:

        content_type = resp.headers.get("Content-Type", "")

        #情况1：直接图片
        if "image" in content_type:
            return await resp.read()

        #情况2：JSON（Cloudflare常见）
        data = await resp.json()

        if "result" in data:

            result = data["result"]

            # Flux返回base64
            if isinstance(result, dict) and "image" in result:
                import base64
                return base64.b64decode(result["image"])

        raise Exception(f"AI返回异常: {data}")

#转换格式
def save_temp_image(image_bytes):

    file_name = f"ai_{random.randint(100000,999999)}.jpg"
    file_path = os.path.join(TMP_DIR, file_name)

    img = Image.open(io.BytesIO(image_bytes))

    if img.mode != "RGB":
        img = img.convert("RGB")

    img.save(
        file_path,
        "JPEG",
        quality=95,
        subsampling=0
    )

    return os.path.abspath(file_path)

# 删除临时文件
async def cleanup_file(path):

    await asyncio.sleep(10)

    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

# 主入口
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

            print(f"[TextToImage] 原始图片大小: {len(image_data)/1024:.2f} KB")

            file_path = save_temp_image(image_data)

            await actions.send(
                **send_kwargs,
                message=Manager.Message(
                    Segments.Image(f"file:///{file_path}")
                )
            )

            asyncio.create_task(cleanup_file(file_path))

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
