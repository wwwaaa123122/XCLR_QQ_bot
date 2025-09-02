from Hyper import Configurator
import random

Configurator.cm = Configurator.ConfigManager(
    Configurator.Config(file="config.json").load_from_file()
)

TRIGGHT_KEYWORD = "Any"
HELP_MESSAGE = "发送『banme』给你禁言600~18000秒"

async def on_message(event, actions, Events, Manager, Segments):
    if isinstance(event, Events.GroupMessageEvent):
        if str(event.message) == "banme":
            bantime = random.randint(600, 18000)  # 取60到300的整数
            await actions.set_group_ban(group_id=event.group_id,user_id=event.user_id,duration=bantime)
            await actions.send(group_id=event.group_id,message=Manager.Message(Segments.Text(f"满足你")))
            return True