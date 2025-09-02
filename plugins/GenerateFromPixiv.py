from Hyper import Configurator
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())
import aiohttp, os, asyncio
from Tools.capture_screenshot import capture_screenshot

reminder = Configurator.cm.get_cfg().others["reminder"]
bot_name = Configurator.cm.get_cfg().others["bot_name"]
TRIGGHT_KEYWORD = "生图 Pixiv "
HELP_MESSAGE = f"{reminder}生图 Pixiv (标签，必填，用&分割) —> {bot_name}浏览P站"

async def on_message(event, actions, Manager, Segments, order, time, cooldowns1, 
                     traceback, datetime, bot_name, generating):
    
    global reminder
    start_index = order.find("生图 Pixiv ")
    selfID = await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text(f"{bot_name}正在从 Pixiv 生成 ヾ(≧▽≦*)o")))
        
    if start_index != -1:
        if not generating:
            user_id = event.user_id
            current_time = time.time()

            if user_id in cooldowns1 and current_time - cooldowns1[user_id] < 5:
                time_remaining1 = 5 - (current_time - cooldowns1[user_id])
                await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text(f"5秒个人cd，请等待 {time_remaining1:.1f} 秒后重试")))
                return
            else:
                generating = True
                result = order[start_index + len("生图 Pixiv "):].strip()
                url_setted = "https://api.lolicon.app/setu/v2?num=1&r18=0&excludeAI=false"

                tags = result.split("&")
                for TagIndex in range(len(tags)):
                    url_setted = url_setted + "&tag=" + tags[TagIndex]

                # 请求API（带重试机制）
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        async with aiohttp.ClientSession(
                            connector=aiohttp.TCPConnector(ssl=False),
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as session:
                            async with session.get(url=url_setted) as response:
                                request = await response.json()
                                break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            request = "Failed\n" + traceback.format_exc()
                        await asyncio.sleep(5)

                if "Failed" in request:
                    await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text(f"{bot_name}无法访问接口了，请稍后重试 ε(┬┬﹏┬┬)3")))
                else:
                    data_normal = request['data']
                    if len(data_normal) < 1:
                        await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text(f"你给{bot_name}的标签太严格啦！（生气），换几个标签试试吧 ＞﹏＜")))
                    else:
                        data = data_normal[0]
                        info = f"""标题：{data['title']}
Pixiv ID：{data['pid']}
作者：{data['author']}
作者ID：{data['uid']}
AI参与：{'是' if data['aiType'] == 1 else '否'}
创作时间：{datetime.datetime.fromtimestamp(data['uploadDate'] / 1000).strftime('%Y-%m-%d')}
标签：{data['tags']}
源图：{data['urls']['original'].replace("pixiv.t.sr-studio.top", "i.pximg.net")}"""
                        url = str(data['urls']['original'])

                        # 检查敏感标签
                        censored_words = ["WinHex", "WinHex"]
                        
                        if not any(word in data['tags'] for word in censored_words):
                            try:
                                # 下载图片到本地
                                local_path = await capture_screenshot(url, "pixiv_image", "png")
                                
                                # 发送本地图片
                                await actions.send(
                                    group_id=event.group_id,
                                    message=Manager.Message(Segments.Image(file=local_path))
                                )
                                
                                # 发送图片信息
                                await actions.send(
                                    group_id=event.group_id,
                                    message=Manager.Message(Segments.Text(info))
                                )
                                
                                # 清理
                                os.remove(local_path)
                                cooldowns1[user_id] = current_time
                                
                            except Exception as e:
                                await actions.send(
                                    group_id=event.group_id,
                                    message=Manager.Message(Segments.Text(f"图片发送失败: {str(e)}"))
                            )
                        else:
                            await actions.send(
                                group_id=event.group_id,
                                message=Manager.Message(Segments.Text(f"你要的图片实在太涩啦！{bot_name}都不敢看了 (⓿_⓿)"))
                            )
                
                generating = False
        else:
            await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text("前面还有一张图在生成呢，请稍候再试吧 (*/ω＼*)")))                       

    else:
        await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Text(f"没有参数。")))

    return True