from Hyper import Configurator 
import asyncio 
import json 
import os 
import random   
from datetime import datetime 
from Hyper import Manager, Segments 
  
 # 加载配置 
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file()) 
  
 # 插件信息 
HELP_MESSAGE = "发送【超我】或【超市我】可以给你的QQ名片点赞10次" 
TRIGGHT_KEYWORD = "Any"   
  
class SuperManager: 
    def __init__(self): 
        self.data_file = "like_data.json" 
        self.user_data = {} 
        self.load_data() 
      
    def load_data(self): 
        try: 
            with open(self.data_file, "r", encoding="utf-8") as f: 
                self.user_data = json.load(f) 
        except (FileNotFoundError, json.JSONDecodeError): 
            self.user_data = {} 
      
    def save_data(self): 
        with open(self.data_file, "w", encoding="utf-8") as f: 
            json.dump(self.user_data, f, ensure_ascii=False, indent=2) 
      
    def can_super_today(self, user_id): 
        user_id = str(user_id) 
        today = datetime.now().strftime("%Y-%m-%d") 
          
        if user_id not in self.user_data: 
            self.user_data[user_id] = {"last_date": today, "count": 0} 
            return True 
          
        if self.user_data[user_id].get("last_date") != today: 
            self.user_data[user_id] = {"last_date": today, "count": 0} 
            return True 
          
        return self.user_data[user_id].get("count", 0) < 10 
      
    def get_remaining_supers(self, user_id): 
        user_id = str(user_id) 
        today = datetime.now().strftime("%Y-%m-%d") 
          
        if user_id not in self.user_data or self.user_data[user_id].get("last_date") != today: 
            return 10 
          
        return 10 - self.user_data[user_id].get("count", 0) 
      
    def record_super(self, user_id, times=1): 
        user_id = str(user_id) 
        today = datetime.now().strftime("%Y-%m-%d") 
          
        if user_id not in self.user_data or self.user_data[user_id].get("last_date") != today: 
            self.user_data[user_id] = {"last_date": today, "count": times} 
        else: 
            self.user_data[user_id]["count"] = self.user_data[user_id].get("count", 0) + times 
          
        self.save_data() 
      
    def get_super_info(self, user_id): 
        user_id = str(user_id) 
        today = datetime.now().strftime("%Y-%m-%d") 
          
        if user_id not in self.user_data or self.user_data[user_id].get("last_date") != today: 
            return "你今天还没有被超过哦！今日还可超10次~" 
          
        count = self.user_data[user_id].get("count", 0) 
        return f"你今天已被超 {count} 次！\n剩余可超次数: {10 - count}次" 
  
super_manager = SuperManager() 
  
async def on_message(event, actions, Manager, Segments): 
    if not hasattr(event, "message") or not hasattr(event, "user_id"): 
        return False 
      
    msg = str(event.message).strip() 
    reminder = Configurator.cm.get_cfg().others["reminder"] 
    bot_name = Configurator.cm.get_cfg().others["bot_name"] 
      
     # 精确匹配"超我"或"超湿我"触发词 
    if msg in ["超我", "超死我", "超市我","赞我"]: 
        user_id = event.user_id 
          
        if not super_manager.can_super_today(user_id): 
            await actions.send( 
                group_id=event.group_id if hasattr(event, "group_id") else None, 
                user_id=user_id if not hasattr(event, "group_id") else None, 
                message=Manager.Message(Segments.Text("今天已经超你10次啦，明天再来吧~ (๑•́ ₃ •̀๑)")) 
            ) 
            return True 
          
        try: 
             # 分5次点赞，每次10赞，共50赞，随机间隔0.1~0.5秒 
            for i in range(5): 
                await actions.custom.send_like(user_id=user_id, times=10) 
                delay = random.uniform(0.1, 0.5)  # 随机延迟0.1~0.5秒 
                await asyncio.sleep(delay) 
              
            super_manager.record_super(user_id, 10)  # 记录为10次 
              
            remaining = super_manager.get_remaining_supers(user_id) 
            success_msg = "已经为你超了10下哦，记得回捏~ (◍•ᴗ•◍)❤" 
            if remaining > 0: 
                success_msg += f"\n今日还可超{remaining}次" 
            else: 
                success_msg += "\n今日超已达上限啦~" 
              
            await actions.send( 
                group_id=event.group_id if hasattr(event, "group_id") else None, 
                user_id=user_id if not hasattr(event, "group_id") else None, 
                message=Manager.Message(Segments.Text(success_msg)) 
            ) 
              
            if hasattr(event, "group_id"): 
                await actions.send( 
                    group_id=event.group_id, 
                    message=Manager.Message( 
                        Segments.At(user_id), 
                        Segments.Text(f"你已被{bot_name}超了10下！(≧▽≦)/") 
                    ) 
                ) 
        except Exception as e: 
            print(f"超操作失败: {e}") 
            await actions.send( 
                group_id=event.group_id if hasattr(event, "group_id") else None, 
                user_id=user_id if not hasattr(event, "group_id") else None, 
                message=Manager.Message(Segments.Text(f"超操作失败啦...可能是机器人没有权限(｡•́︿•̀｡) 错误: {str(e)}")) 
            ) 
        return True 
      
     # 保留带前缀的"超信息"查询功能 
    elif msg == f"{reminder}超信息": 
        user_id = event.user_id 
        info = super_manager.get_super_info(user_id) 
          
        await actions.send( 
            group_id=event.group_id if hasattr(event, "group_id") else None, 
            user_id=user_id if not hasattr(event, "group_id") else None, 
            message=Manager.Message(Segments.Text(info)) 
        ) 
        return True 
      
    return False 
  
print("[QQ名片超插件] 加载成功") 
print("触发词: 超我, 超市我") 
print("功能: 每次给用户QQ名片点赞10次，每日上限10次")
