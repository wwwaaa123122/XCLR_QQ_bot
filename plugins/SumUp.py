import re, os
import google.generativeai as genai
from collections import defaultdict, deque
import pickle, gc
from Hyper import Configurator, Events
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())

TRIGGHT_KEYWORD = "Any"
HELP_MESSAGE = f'''{Configurator.cm.get_cfg().others["reminder"]}总结以上N条消息 —> 总结当前群聊的指定数量的消息 (0<N<=1000)'''
genai.configure(api_key=Configurator.cm.get_cfg().others["gemini_key"])
model = genai.GenerativeModel('gemini-2.5-flash') 

def default_factory():
    return {
        "history": deque(maxlen=1000),  
        "token_counter": 0 
    }
chat_db = defaultdict(default_factory)

# 估算Token（中文≈1字/Tok，英文≈1词/4字母）
def estimate_tokens(text: str) -> int:
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    non_chinese = len(text) - chinese_chars
    return chinese_chars + (non_chinese // 4) + 1

def add_message(group_id: str, user: str, content: str, chat_db=chat_db):
    """添加消息并更新Token计数"""
    tokens = estimate_tokens(f"{user}: {content}")
    chat_db[group_id]["history"].append({"user": user, "content": content})
    chat_db[group_id]["token_counter"] += tokens
    return chat_db

def max_summarizable_msgs(group_id: str, max_tokens=800000) -> int:
    """计算当前群聊最多可总结的消息条数"""
    history = chat_db[group_id]["history"]
    total_tokens = 0
    count = 0
    # 从最新消息向前回溯，直到Token超限
    for msg in reversed(history):
        msg_tokens = estimate_tokens(f"{msg['user']}: {msg['content']}")
        if total_tokens + msg_tokens > max_tokens:
            break
        total_tokens += msg_tokens
        count += 1
    return count

def handle_summary_request(group_id: str, match, chat_db=chat_db):
    """处理用户总结请求（如：'总结以上100条消息'）"""
    try:
        n = int(match.group(1))
        if n <= 0 or n > 1000:
            return "❌ 命令格式错误！请用：'总结以上N条消息' (0<N<=1000)"
        
        total_tokens = sum(estimate_tokens(f"{msg['user']}: {msg['content']}") 
                        for msg in list(chat_db[group_id]["history"])[-n:])
        max_tokens = 800000  # 预留20%缓冲
        if total_tokens > max_tokens:
            max_n = max_summarizable_msgs(group_id)
            return f"⚠️ 消息过长（{total_tokens} Tokens > 上限{max_tokens}）\n最多可总结{max_n}条消息"
        
        if len(list(chat_db[group_id]["history"])) < 10:
            return "⚠️ 消息过少（少于 10 条消息）"
        
        messages = "\n".join(f"{msg['user']}: {msg['content']}" for msg in list(chat_db[group_id]["history"])[-n:])
        prompt = f'''你是一个专业的聊天总结助手，需要根据以下群聊记录生成摘要：
        
### 聊天记录：
{messages}
        
### 总结要求：
1. 用紧凑的格式呈现，少于{max_tokens // 10}个汉字
2. 关键点或关键决策点需加粗
3. 标注提出重要意见的成员
4. 如果有，请列出未解决的问题
5. 总结后给出建议或方案
6. 尽量不要使用 Markdown 格式'''

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 总结时发生异常：\n{e}"

def handle_node_messages(data: dict):
    temp_db = defaultdict(lambda: {
        "history": deque(maxlen=1000),  
        "token_counter": 0 
    })
    
    for message_node in data['message']:
        if message_node.get('type') == 'node':
            node_data = message_node.get('data', {})
            nickname = node_data.get('nickname', node_data.get('user_id', ''))
            content_list = node_data.get('content', [])
            
            text_parts = []
            for content_item in content_list:
                if content_item.get('type') == 'text':
                    text_data = content_item.get('data', {})
                    text = text_data.get('text', '')
                    if text:
                        text_parts.append(text)
                        
            full_text = ''.join(text_parts)
            if full_text:
                print(f"SumUp: 添加群聊消息 {nickname}: {full_text} 到临时数据库")
                temp_db = add_message(0, nickname, full_text, temp_db)
                
    return temp_db
    
async def get_user_info(uid, Manager, actions):
    try:
        gc.collect()
        for _ in range(6):
            info = Manager.Ret.fetch(await actions.custom.get_stranger_info(user_id=uid, no_cache=True))
            if 'nickname' not in info.data.raw:
                raise ValueError(f"{uid} is not a valid user ID.")
            if str(info.data.raw.get('user_id', '未知')) == str(uid):
                break
        
        return True, info.data.raw
    except Exception as e:
        print(f"SumUp: 获取用户 {uid} 信息失败: {e}")
        return False, str(uid)
    
async def get_user_nickname(uid, Manager, actions) -> str:
    s, user_info = await get_user_info(uid, Manager, actions)
    if s:
        return f"@{user_info['nickname']}"
    else:
        return str(uid)
    
async def on_message(event, actions, Manager, Events, Segments, bot_name, gen_message):
    global chat_db
    if not isinstance(event, Events.GroupMessageEvent):
        return None
    
    message: str = ""
    user_message = str(event.message).strip()
    match = re.search(r"总结(?:以上|最近)?(\d+)(?:条|个)?消息", user_message)
    if match:
        selfID = await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text(f"请等待，{bot_name} 正在总结消息......φ(゜▽゜*)♪")))
        if isinstance(event.message[0], Segments.Reply):
            content = await actions.get_msg(event.message[0].id)
            msg = gen_message({"message": content.data["message"]})
            for i in msg:
                if isinstance(i, Segments.Forward):
                    data = Manager.Ret.fetch(await actions.custom.get_forward_msg(id=i.id)).data.raw
                    message = handle_summary_request(0, match, handle_node_messages(data))
                    break
                
            if not message:
                message = "❌ 未找到转发的消息！\n请确保引用消息的是一条聊天记录，并确保消聊天记录中包含需要总结的消息"
        else:
            message = handle_summary_request(event.group_id, match)
            
        if len(message) < 400:
            await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Reply(event.message_id), Segments.Text(message)))
        else:
            await actions.send_group_forward_msg(
                group_id=event.group_id,
                message=Manager.Message(Segments.CustomNode(
                                        str(event.self_id),
                                        bot_name,
                                        Manager.Message(Segments.Text(message))
                    )
                )
            )
        await actions.del_message(selfID.data.message_id)
        return True
    else:
        if event.group_id not in chat_db:
            print(f"SumUp: 群组 {event.group_id} 不存在于`chat_db`中，将初始化")
            
        nike = await get_user_nickname(event.user_id, Manager, actions)
        chat_db = add_message(event.group_id, nike, user_message)
        
        # 调试日志：显示添加后的状态
        print(f"SumUp: 添加ID为 {event.user_id} 的用户 {nike} 的信息到数据库，现有 {len(chat_db[event.group_id]['history'])} 条消息")
        
        try:
            with open(os.path.join("data",'sum_up', 'chat_db.pkl'), 'wb') as f:
                pickle.dump(chat_db, f)
        except Exception as e:
            print(f"SumUp: 保存聊天记录失败: {e}")
            
        return None
    
if os.path.exists(os.path.join("data",'sum_up', 'chat_db.pkl')) and os.path.getsize(os.path.join("data",'sum_up', 'chat_db.pkl')) > 0:
    try:
        with open(os.path.join("data",'sum_up', 'chat_db.pkl'), 'rb') as f:
            loaded_db = pickle.load(f)
            print(f"SumUp: 成功加载 {len(loaded_db)} 个群聊的历史消息")
            # 保留已存在的群组数据，只更新新增的
            for group_id in loaded_db:
                if group_id not in chat_db:
                    chat_db[group_id] = loaded_db[group_id]
            print(f"SumUp: 合并后共有 {len(chat_db)} 个群聊的历史消息")
    except Exception as e:
        print(f"SumUp: 加载历史消息失败: {e}")