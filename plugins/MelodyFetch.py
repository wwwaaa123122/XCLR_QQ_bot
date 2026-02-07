# -*- coding: utf-8 -*-
import aiohttp
import asyncio
import os
import re
from urllib.parse import quote
from functools import wraps

IS_PRIVATE_ENABLED = True
TRIGGHT_KEYWORD = "点歌"
HELP_MESSAGE = f"#点歌 [歌名] —> 搜索网易云音乐歌曲\n#点歌 [ID] —> 根据ID获取歌曲"
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 1  # 重试延迟(秒)

def retry_async_request(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """异步请求重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

async def on_message(event, actions, Manager, Segments, reminder):
    try:
        # 获取用户消息内容
        user_message = str(event.message)
        
        # 获取 group_id 或 user_id
        send_id = getattr(event, "group_id", None) or getattr(event, "user_id", None)
        
        # 检查是否包含完整的触发关键词（包括reminder）
        full_trigger = f"{reminder}{TRIGGHT_KEYWORD}"
        if not user_message.startswith(full_trigger):
            return False
            
        # 提取歌名或ID
        content = user_message[len(full_trigger):].strip()
        
        if not content:
            await actions.send(
                group_id=send_id,
                message=Manager.Message(Segments.Text("唔…宝宝想听什么歌呀？要告诉星辰旅人歌名或者ID才可以哦～(。•ω•。)ﾉ\n例如：#点歌 晴天 或者 #点歌 2652820720"))
            )
            return True
        
        # 判断是搜索歌曲还是通过ID获取
        if content.isdigit():
            # 通过ID获取歌曲
            await get_song_by_id(content, event, actions, Manager, Segments, send_id)
        else:
            # 搜索歌曲
            await search_songs(content, event, actions, Manager, Segments, send_id)
            
        return True
        
    except Exception as e:
        error_msg = f"点歌功能出现错误: {str(e)}"
        print(error_msg)
        send_id = getattr(event, "group_id", None) or getattr(event, "user_id", None)
        await actions.send(
            group_id=send_id,
            message=Manager.Message(Segments.Text("呜呜…点歌功能好像出了点小问题呢(╥﹏╥) 主人等一会再试试吧。"))
        )
        return True

@retry_async_request()
async def search_api_request(url):
    """搜索API请求（带重试）"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API返回状态码: {response.status}")

async def search_songs(keyword, event, actions, Manager, Segments, send_id):
    """搜索歌曲"""
    try:
        encoded_keyword = quote(keyword)
        url = f"https://api.vkeys.cn/v2/music/netease?word={encoded_keyword}&page=1&num=10"
        
        data = await search_api_request(url)
        
        if data.get("code") == 200 and data.get("data"):
            songs = data["data"]
            result_text = f"🎵 宝宝~帮你找到这些歌曲哦！你想听哪一首呀？(◍•ᴗ•◍)❤\n\n"
            
            for i, song in enumerate(songs[:5]):  # 只显示前5首
                result_text += f"{i+1}. {song['song']} - {song['singer']} (ID: {song['id']})\n"
            
            result_text += f"\n✨ 发送 '#点歌 ID' 就可以听到啦～比如: #点歌 {songs[0]['id']} 这样哦！(≧∇≦)ﾉ"
            
            await actions.send(
                group_id=send_id,
                message=Manager.Message(Segments.Text(result_text))
            )
        else:
            await actions.send(
                group_id=send_id,
                message=Manager.Message(Segments.Text("呜…没有找到相关的歌曲呢(；ω；`) 宝宝换个关键词试试看嘛～"))
            )
                    
    except asyncio.TimeoutError:
        await actions.send(
            group_id=send_id,
            message=Manager.Message(Segments.Text("搜索超时啦～网络可能有点慢呢(´･ω･`) 宝宝耐心等一下哦！"))
        )
    except Exception as e:
        print(f"搜索歌曲时出错: {e}")
        await actions.send(
            group_id=send_id,
            message=Manager.Message(Segments.Text("搜索服务出了点小问题呢(>_<) 星辰旅人马上检查一下，宝宝稍等哦～"))
        )

@retry_async_request()
async def song_info_api_request(url):
    """歌曲信息API请求（带重试）"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API返回状态码: {response.status}")

async def get_song_by_id(song_id, event, actions, Manager, Segments, send_id):
    """通过ID获取歌曲详情和下载链接"""
    try:
        url = f"https://api.vkeys.cn/v2/music/netease?id={song_id}"
        
        data = await song_info_api_request(url)
        
        if data.get("code") == 200 and data.get("data"):
            song_data = data["data"]
            
            # 检查文件大小（10MB限制）
            size_str = song_data.get("size", "0MB")
            size_match = re.search(r"(\d+\.?\d*)MB", size_str)
            size_mb = float(size_match.group(1)) if size_match else 0
            
            # 构建消息内容
            song_info = f"""🎵 歌曲: {song_data['song']}
👤 歌手: {song_data['singer']}
💿 专辑: {song_data['album']}
⏱ 时长: {song_data.get('interval', '未知')}
🔗 链接: {song_data.get('url', '无')}"""
            
            # 添加文件大小信息
            if size_mb > 0:
                song_info += f"\n📦 大小: {size_str}"
            
            # 发送封面图片
            if song_data.get('cover'):
                try:
                    await actions.send(
                        group_id=send_id,
                        message=Manager.Message(Segments.Image(song_data['cover']))
                    )
                    await asyncio.sleep(0.5)  # 稍微延迟一下
                except:
                    print("发送封面图片失败")
            
            # 发送歌曲信息
            await actions.send(
                group_id=send_id,
                message=Manager.Message(Segments.Text(f"找到啦！这是宝宝要听的歌哦～(ノ◕ヮ◕)ノ*:･ﾟ✧\n\n{song_info}"))
            )
            
            # 检查文件大小，超过70MB不发送音乐文件
            if size_mb > 70:
                await actions.send(
                    group_id=send_id,
                    message=Manager.Message(Segments.Text("⚠️ 啊这个音乐太~太大了呢(´•̥ ̯ •̥`) 超过星辰旅人能承受的极限啦，星辰旅人发不了音频文件呢…但是宝宝可以点开链接听哦！"))
                )
            else:
                # 下载并发送音乐文件
                download_url = song_data.get('url')
                if download_url:
                    await download_and_send_music(download_url, event, actions, Manager, Segments, send_id)
                else:
                    await actions.send(
                        group_id=send_id,
                        message=Manager.Message(Segments.Text("呜呜…找不到下载链接呢(；´Д｀) 宝宝换个ID试试看嘛～"))
                    )
        else:
            await actions.send(
                group_id=send_id,
                message=Manager.Message(Segments.Text("咦？这个ID好像不对呢(´･ω･`) 宝宝检查一下ID是否正确哦～"))
            )
                    
    except asyncio.TimeoutError:
        await actions.send(
            group_id=send_id,
            message=Manager.Message(Segments.Text("获取信息超时啦～网络可能有点卡呢(´･ω･`) 宝宝耐心等一下哦！"))
        )
    except Exception as e:
        print(f"获取歌曲信息时出错: {e}")
        await actions.send(
            group_id=send_id,
            message=Manager.Message(Segments.Text("获取信息出了点问题呢(>_<) 星辰旅人马上检查一下，宝宝稍等哦～"))
        )

@retry_async_request(max_retries=2)  # 下载重试次数少一些
async def download_music_file(url, temp_file):
    """下载音乐文件（带重试）"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                file_size = 0
                with open(temp_file, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        file_size += len(chunk)
                        
                        # 检查文件大小是否超过70MB
                        if file_size > 70 * 1024 * 1024:
                            f.close()
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                            raise Exception("文件大小超过70MB限制")
                
                # 检查最终文件大小
                if os.path.getsize(temp_file) > 10 * 1024 * 1024:
                    os.remove(temp_file)
                    raise Exception("文件大小超过10MB限制")
                
                return True
            else:
                raise Exception(f"下载失败，状态码: {response.status}")

async def download_and_send_music(url, event, actions, Manager, Segments, send_id):
    """下载并发送音乐文件"""
    try:
        # 创建临时目录
        temp_dir = "temp_music"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # 生成临时文件名
        temp_file = os.path.join(temp_dir, f"music_{getattr(event, 'message_id', 'temp')}.mp3")
        
        # 先发送一个等待消息
        await actions.send(
            group_id=send_id,
            message=Manager.Message(Segments.Text("正在为宝宝下载歌曲哦～请稍等一下下(◕‿◕)♡"))
        )
        
        # 下载文件（带重试）
        await download_music_file(url, temp_file)
        
        # 发送音乐文件
        await actions.send(
            group_id=send_id,
            message=Manager.Message(Segments.Text("下载完成啦！马上给宝宝发送哦～♪(^∇^*)"))
        )
        await actions.send(
            group_id=send_id,
            message=Manager.Message(Segments.Record(temp_file))
        )
        
        # 删除临时文件（延迟删除确保发送完成）
        await asyncio.sleep(2)
        if os.path.exists(temp_file):
            os.remove(temp_file)
                    
    except asyncio.TimeoutError:
        await actions.send(
            group_id=send_id,
            message=Manager.Message(Segments.Text("下载超时啦～网络可能有点慢呢(´･ω･`) 宝宝耐心等一下哦！"))
        )
    except Exception as e:
        print(f"下载歌曲时出错: {e}")
        error_msg = str(e)
        if "文件大小超过10MB限制" in error_msg:
            await actions.send(
                group_id=send_id,
                message=Manager.Message(Segments.Text("⚠️ 啊这个音乐太~太大了呢(´•̥ ̯ •̥`) 超过星辰旅人能承受的极限啦，星辰旅人发不了音频文件呢…但是宝宝可以点开链接听哦！"))
            )
        else:
            await actions.send(
                group_id=send_id,
                message=Manager.Message(Segments.Text("下载出了点问题呢(>_<) 星辰旅人马上检查一下，宝宝稍等哦～"))
            )
        
        # 清理临时文件
        temp_dir = "temp_music"
        for file in os.listdir(temp_dir):
            temp_file = os.path.join(temp_dir, file)
            if os.path.isfile(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
