from Hyper import Configurator
import requests
import json
import os
from datetime import datetime

Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "天气"
HELP_MESSAGE = f"{Configurator.cm.get_cfg().others['reminder']}天气 城市名 —> 查询指定城市的天气信息，包括今明后三天预报哦~"

API_URL = 'http://apis.juhe.cn/simpleWeather/query'
API_KEY = '8eead4bb604f96eff59c78be4bf7c39f'  # 请替换为你的聚合数据API Key

# 创建数据存储目录
WEATHER_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'weather'))
os.makedirs(WEATHER_DATA_DIR, exist_ok=True)

def get_user_data_path(user_id):
    """获取用户数据文件路径"""
    return os.path.join(WEATHER_DATA_DIR, f"{user_id}.json")

def load_user_data(user_id):
    """加载用户数据"""
    user_file = get_user_data_path(user_id)
    if os.path.exists(user_file):
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"count": 0, "last_used": ""}
    return {"count": 0, "last_used": ""}

def save_user_data(user_id, data):
    """保存用户数据"""
    user_file = get_user_data_path(user_id)
    try:
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存用户天气数据失败: {e}")

def update_weather_usage(user_id):
    """更新用户使用次数"""
    user_data = load_user_data(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 如果是今天第一次使用
    if user_data["last_used"] != today:
        user_data["count"] += 1
    
    user_data["last_used"] = today
    save_user_data(user_id, user_data)
    return user_data["count"]

# 辅助函数，尝试将值转为整数
def try_parse_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

async def on_message(event, actions, Manager, Segments, reminder, bot_name):
    msg = str(event.message)
    prefix = f"{reminder}天气"

    # 判断是否是群聊（检查 event 是否有 group_id 属性且不为 None）
    is_group = hasattr(event, 'group_id') and event.group_id is not None

    # 检查是否是群聊且以reminder前缀开头，或者是私聊且包含天气关键词
    if is_group:
        if not msg.startswith(prefix):
            return False
        city_query = msg[len(prefix):].strip()
    else:
        # 私聊模式：检查是否包含"天气"关键词
        if "天气" not in msg:
            return False
        # 移除reminder前缀（如果有）
        if msg.startswith(reminder):
            city_query = msg[len(reminder):].replace("天气", "", 1).strip()
        else:
            city_query = msg.replace("天气", "", 1).strip()

    # 获取 group_id 或 user_id
    if is_group:
        send_id = event.group_id
    else:
        send_id = getattr(event, "user_id", None)

    # 更新用户使用次数
    usage_count = update_weather_usage(str(event.user_id))
    if not city_query:
        # 根据群聊或私聊选择正确的参数
        if is_group:
            await actions.send(group_id=send_id, message=Manager.Message(
                Segments.Reply(event.message_id) if hasattr(event, "message_id") else None,
                Segments.Text(f"小可爱，忘记输入城市名字啦！例如：{reminder}天气 北京 (づ｡◕‿‿◕｡)づ")
            ))
        else:
            await actions.send(user_id=send_id, message=Manager.Message(
                Segments.Text(f"小可爱，忘记输入城市名字啦！例如：天气 北京 (づ｡◕‿‿◕｡)づ")
            ))
        return True
    
    params = {
        'key': API_KEY,
        'city': city_query,
    }
    
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('error_code') == 0:
                result = data.get('result', {})
                realtime = result.get('realtime', {})
                future_weather = result.get('future', [])
                city_name = result.get('city', '未知城市')

                temp_str = realtime.get('temperature', '??')
                humidity_str = realtime.get('humidity', '??')
                info = realtime.get('info', '晴朗')
                direct = realtime.get('direct', '微风')
                power = realtime.get('power', '轻轻吹')
                aqi_str = realtime.get('aqi', '??')

                temp_val = try_parse_int(temp_str)
                humidity_val = try_parse_int(humidity_str) # 假设API返回的湿度是不带%的数字字符串
                aqi_val = try_parse_int(aqi_str)

                cute_message_parts = [f"喵~ {city_name}的实时天气来咯！✧٩(ˊωˋ*)و✧"]

                # 添加使用次数信息
                cute_message_parts.append(f"✨ 这是你本月第 {usage_count} 次查询天气啦！")

                # 天气状况判断
                if "晴" in info:
                    cute_message_parts.append(f"☀️ 今天是大晴天，{info}！心情也要阳光起来呀！")
                elif "多云" in info:
                    cute_message_parts.append(f"🌥️ 现在是{info}，偶尔能见到太阳公公哦~")
                elif "阴" in info:
                    cute_message_parts.append(f"☁️ {info}天啦，不过也要保持好心情呀！")
                elif "雨" in info:
                    cute_message_parts.append(f"🌧️ 下{info}啦！出门记得带上心爱的小雨伞哦~")
                elif "雪" in info:
                    cute_message_parts.append(f"❄️ 哇！下{info}了！可以堆雪人打雪仗啦！")
                else:
                    cute_message_parts.append(f"ฅ 天气宝宝说：现在是 {info} 哦！")

                # 温度判断
                if temp_val is not None:
                    if temp_val < 10:
                        cute_message_parts.append(f"🌡️ 温度：{temp_str}°C (有点冷哦，快穿上暖暖的衣服！🧥)")
                    elif temp_val <= 25:
                        cute_message_parts.append(f"🌡️ 温度：{temp_str}°C (温度刚刚好，超舒服的！😊)")
                    else:
                        cute_message_parts.append(f"🌡️ 温度：{temp_str}°C (热乎乎的，记得防晒补水哦！☀️)")
                else:
                    cute_message_parts.append(f"🌡️ 温度：{temp_str}°C (暖暖的还是凉凉的？)")

                # 湿度判断
                if humidity_val is not None:
                    if humidity_val < 40:
                        cute_message_parts.append(f"💧 湿度：{humidity_str}% (空气有点小干燥，多喝水！)")
                    elif humidity_val <= 70:
                        cute_message_parts.append(f"💧 湿度：{humidity_str}% (湿度刚刚好，皮肤润润的！)")
                    else:
                        cute_message_parts.append(f"💧 湿度：{humidity_str}% (空气有点湿润，感觉清新~)")
                else:
                    cute_message_parts.append(f"💧 湿度：{humidity_str}% (空气湿润吗？)")
                
                cute_message_parts.append(f"🍃 风儿：{direct} {power} (记得带伞或帽子哦！)")

                # AQI 判断
                if aqi_val is not None:
                    if aqi_val <= 50:
                        cute_message_parts.append(f"🌳 空气质量：AQI {aqi_str} (空气超新鲜，深呼吸一下！)")
                    elif aqi_val <= 100:
                        cute_message_parts.append(f"🌳 空气质量：AQI {aqi_str} (空气还不错，可以出门玩耍啦！)")
                    elif aqi_val <= 150:
                        cute_message_parts.append(f"🌳 空气质量：AQI {aqi_str} (敏感的小伙伴要注意防护~)")
                    else:
                        cute_message_parts.append(f"🌳 空气质量：AQI {aqi_str} (空气不太好，出门戴口罩更安心！)")
                else:
                    cute_message_parts.append(f"🌳 空气质量：AQI {aqi_str} (深呼吸一下！)")

                # 未来天气部分保持不变
                if len(future_weather) >= 1:
                    next_day = future_weather[0]
                    next_day_weather = next_day.get('weather', '未知')
                    next_day_temp = next_day.get('temperature', '??/??℃')
                    cute_message_parts.append(f"☀️ 明天会是 {next_day_weather}, 温度在 {next_day_temp} 之间哦! (｡･ω･｡)ﾉ♡")
                else:
                    cute_message_parts.append("☀️ 明天的天气有点神秘，暂时看不到呢~")

                if len(future_weather) >= 2:
                    day_after_next = future_weather[1]
                    day_after_next_weather = day_after_next.get('weather', '未知')
                    day_after_next_temp = day_after_next.get('temperature', '??/??℃')
                    cute_message_parts.append(f"🌤️ 后天呢, {day_after_next_weather}, 温度大约 {day_after_next_temp}~ (＾▽＾)")
                else:
                    cute_message_parts.append("🌤️ 后天的天气也有点神秘，暂时看不到呢~")
                
                cute_message = "\n".join(cute_message_parts)
                # 根据群聊或私聊选择正确的参数
                if is_group:
                    await actions.send(group_id=send_id, message=Manager.Message(
                        Segments.Reply(event.message_id) if hasattr(event, "message_id") else None, 
                        Segments.Text(cute_message)
                    ))
                else:
                    await actions.send(user_id=send_id, message=Manager.Message(
                        Segments.Text(cute_message)
                    ))
            else:
                if is_group:
                    await actions.send(group_id=send_id, message=Manager.Message(
                        Segments.Reply(event.message_id) if hasattr(event, "message_id") else None, 
                        Segments.Text(f"呜呜~ 查询失败了呢：{data.get('reason', '未知错误')} T_T")
                    ))
                else:
                    await actions.send(user_id=send_id, message=Manager.Message(
                        Segments.Text(f"呜呜~ 查询失败了呢：{data.get('reason', '未知错误')} T_T")
                    ))
        else:
            if is_group:
                await actions.send(group_id=send_id, message=Manager.Message(
                    Segments.Reply(event.message_id) if hasattr(event, "message_id") else None, 
                    Segments.Text("哎呀！天气预报卫星好像开小差了，稍后再试试吧！(｡•́︿•̀｡)")
                ))
            else:
                await actions.send(user_id=send_id, message=Manager.Message(
                    Segments.Text("哎呀！天气预报卫星好像开小差了，稍后再试试吧！(｡•́︿•̀｡)")
                ))
    except requests.exceptions.Timeout:
        if is_group:
            await actions.send(group_id=send_id, message=Manager.Message(
                Segments.Reply(event.message_id) if hasattr(event, "message_id") else None, 
                Segments.Text("网络有点慢，天气信息飞不过来啦~稍后再试哦！")
            ))
        else:
            await actions.send(user_id=send_id, message=Manager.Message(
                Segments.Text("网络有点慢，天气信息飞不过来啦~稍后再试哦！")
            ))
    except Exception as e:
        if is_group:
            await actions.send(group_id=send_id, message=Manager.Message(
                Segments.Reply(event.message_id) if hasattr(event, "message_id") else None, 
                Segments.Text(f"程序兽遇到了一点小麻烦：{e}，快叫主人来看看！QAQ")
            ))
        else:
            await actions.send(user_id=send_id, message=Manager.Message(
                Segments.Text(f"程序兽遇到了一点小麻烦：{e}，快叫主人来看看！QAQ")
            ))
    return True 

# 插件加载时打印信息
print("[天气查询插件] 已成功加载")
print(f"数据存储路径: {WEATHER_DATA_DIR}")
print(f"触发关键词: {TRIGGHT_KEYWORD}")
print("功能: 查询城市天气信息并记录用户使用次数")