import json
import time
import traceback
import requests
from Tools.AI_tools import *

class network_gpt():
    def __init__(self, prompt, message, user_lists, uid, account_id, bn, auth_token) -> None:
        self.prompt = prompt
        self.message = message
        self.user_lists = user_lists
        self.uid = uid
        self.account_id = "2228d557489e8da66c733ca71f6e5729"
        self.auth_token = "_icVsni2kwZRZPBaxrM465QZav8XhGaHob7PMvSt"
        self.bn = bn
        self.model = "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{self.model}"

    def Response(self):
        try:
            input_data = self.message
            user_lists = self.user_lists

            if str(self.uid) not in user_lists:
                user_lists[str(self.uid)] = []

            user_input: list = user_lists[str(self.uid)]

            if len(user_input) >= 15:
                user_input.pop(0)
                user_input.pop(0)
                user_input.pop(0)

            user_input.append({"role": "system","content": self.prompt})
            user_input.append({"role": "user", "content": input_data})

            print(str(self.uid) + " 的上下文：" + str(len(user_input)))

            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "messages": user_input,
                "stream": True,
                "max_tokens": 4096
            }

            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    stream=True
                )

                if response.status_code != 200:
                    error_msg = f"API错误 ({response.status_code}): {response.text}"
                    yield error_msg, 'message'
                    return

                def cloudflare_stream_generator():
                    for line in response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data: '):
                                data = line_str[6:]
                                if data == '[DONE]':
                                    break
                                try:
                                    json_data = json.loads(data)
                                    if 'response' in json_data:
                                        yield {'choices': [{'delta': {'content': json_data['response']}}]}
                                except json.JSONDecodeError:
                                    continue

                splitter = StreamSplitter()
                for message, _ in splitter.split_stream(cloudflare_stream_generator(), 'openai'):
                    print(f"[{time.time()}] YIELD: {repr(message)}")
                    yield message, 'message'

                user_input.append({"role": "assistant", "content": splitter.full_content})
                user_lists[str(self.uid)] = user_input
                yield user_lists, 'user_lists'

            except requests.exceptions.RequestException as e:
                error_response = str(e)
                if 'quota' in error_response.lower() or 'limit' in error_response.lower():
                    yield f'''配额已用尽。
{self.bn}发生错误，不能回复你的消息了，请稍候再试吧 ε(┬┬﹏┬┬)3''', 'message'
                else:
                    yield f'''API请求错误: {error_response}
{self.bn}发生错误，不能回复你的消息了，请稍候再试吧 ε(┬┬﹏┬┬)3''', 'message'

        except Exception as e:
            print(traceback.format_exc())
            yield f"{type(e)}\n{self.bn}发生错误，不能回复你的消息了，请稍候再试吧 ε(┬┬﹏┬┬)3", 'message'
