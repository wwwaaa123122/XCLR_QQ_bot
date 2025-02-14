## 插件可供调用的变量
**本文格式：参数名: 参考值（非实际提供值，大部分参数有相应注解注意甄别）**
```python
'__name__': '__main__',

'__annotations__': {
    'emoji_send_count': <module'datetime'from'/usr/lib/python3.12/datetime.py'>,
    'reminder': <class'str'>,
    'ROOT_User': <class'list'>,
    'Super_User': <class'list'>,
    'Manage_User': <class'list'>,
    'sisters': <class'list'>,
    'jhq': <class'list'>
},

'__file__': '/root/Jianer/main.py', #简儿主程序的入口文件路径

# 以下均为内置库或第三方库，详细调用方法请见各个库官方的详细说明。
'faulthandler': <module'faulthandler'(built-in)>,
'asyncio': <module'asyncio'from'/usr/lib/python3.12/asyncio/__init__.py'>,
'datetime': <module'datetime'from'/usr/lib/python3.12/datetime.py'>,
'os': <module'os'(frozen)>,
'importlib': <module'importlib'from'/usr/lib/python3.12/importlib/__init__.py'>,
'sys': <module'sys'(built-in)>,
'inspect': <module'inspect'from'/usr/lib/python3.12/inspect.py'>,
'random': <module'random'from'/usr/lib/python3.12/random.py'>,
'uuid': <module'uuid'from'/usr/lib/python3.12/uuid.py'>,
're': <module're'from'/usr/lib/python3.12/re/__init__.py'>,
'base64': <module'base64'from'/usr/lib/python3.12/base64.py'>,
'urllib': <module'urllib'from'/usr/lib/python3.12/urllib/__init__.py'>,
'emoji': <module'emoji'from'/usr/local/lib/python3.12/dist-packages/emoji/__init__.py'>,
'time': <module'time'(built-in)>,
'traceback': <module'traceback'from'/usr/lib/python3.12/traceback.py'>,
'OpenAI': <class'openai.OpenAI'>,
'requests': <module'requests'from'/usr/lib/python3/dist-packages/requests/__init__.py'>,
'aiohttp': <module'aiohttp'from'/usr/local/lib/python3.12/dist-packages/aiohttp/__init__.py'>,
'Configurator': <module'Hyper.Configurator'from'/usr/local/lib/python3.12/dist-packages/Hyper/Configurator.py'>,
'platform': <module'platform'from'/usr/lib/python3.12/platform.py'>,
'psutil': <module'psutil'from'/usr/lib/python3/dist-packages/psutil/__init__.py'>,
'GPUtil': <module'GPUtil'from'/usr/local/lib/python3.12/dist-packages/GPUtil/__init__.py'>,
'subprocess': <module'subprocess'from'/usr/lib/python3.12/subprocess.py'>,
'Set': typing.Set,
'Image': <module'PIL.Image'from'/usr/local/lib/python3.12/dist-packages/PIL/Image.py'>,
'io': <module'io'(frozen)>,
'threading': <module'threading'from'/usr/lib/python3.12/threading.py'>,
'paramiko': <module'paramiko'from'/usr/local/lib/python3.12/dist-packages/paramiko/__init__.py'>,

'bot_name': '简儿', #机器人的名称
'bot_name_en': 'Jianer', #机器人的英文名称

'Listener': <module'Hyper.Listener'from'/usr/local/lib/python3.12/dist-packages/Hyper/Listener.py'>, 
#事件监听模块，详见[文档](https://harcicyang.github.io/hyper-bot/more/classes.html#listener-%E6%A8%A1%E5%9D%97)

'Events': <module'Hyper.Events'from'/usr/local/lib/python3.12/dist-packages/Hyper/Events.py'>,
#事件类型模块，详见[文档](https://harcicyang.github.io/hyper-bot/more/classes.html#events-%E6%A8%A1%E5%9D%97)

'Logger': <module'Hyper.Logger'from'/usr/local/lib/python3.12/dist-packages/Hyper/Logger.py'>,
#日志类型模块，详见[文档](https://harcicyang.github.io/hyper-bot/more/classes.html#logger-py)

'Manager': <module'Hyper.Manager'from'/usr/local/lib/python3.12/dist-packages/Hyper/Manager.py'>,
#消息内容模块，详见[文档](https://harcicyang.github.io/hyper-bot/more/classes.html#manager-%E6%A8%A1%E5%9D%97)

'Segments': <module'Hyper.Segments'from'/usr/local/lib/python3.12/dist-packages/Hyper/Segments.py'>,
#消息事件模块，详见[文档](https://harcicyang.github.io/hyper-bot/more/classes.html#segments-%E6%A8%A1%E5%9D%97)

'Logic': <module'Hyper.Utils.Logic'from'/usr/local/lib/python3.12/dist-packages/Hyper/Utils/Logic.py'>,
#详见[文档](https://harcicyang.github.io/hyper-bot/more/classes.html#logic-py)

'message_types': {
    'text': {
        'type': <class'Hyper.Segments.Text'>,
        'args': [
            'text'
        ]
    },
    'image': {
        'type': <class'Hyper.Segments.Image'>,
        'args': [
            'file',
            'url',
            'summary'
        ]
    },
    'at': {
        'type': <class'Hyper.Segments.At'>,
        'args': [
            'qq'
        ]
    },
    'reply': {
        'type': <class'Hyper.Segments.Reply'>,
        'args': [
            'id'
        ]
    },
    'face': {
        'type': <class'Hyper.Segments.Faces'>,
        'args': [
            'id'
        ]
    },
    'location': {
        'type': <class'Hyper.Segments.Location'>,
        'args': [
            'lat',
            'lon'
        ]
    },
    'record': {
        'type': <class'Hyper.Segments.Record'>,
        'args': [
            'file',
            'url'
        ]
    },
    'video': {
        'type': <class'Hyper.Segments.Video'>,
        'args': [
            'file',
            'url'
        ]
    },
    'poke': {
        'type': <class'Hyper.Segments.Poke'>,
        'args': [
            'type',
            'id'
        ]
    },
    'contact': {
        'type': <class'Hyper.Segments.Contact'>,
        'args': [
            'type',
            'id'
        ]
    },
    'forward': {
        'type': <class'Hyper.Segments.Forward'>,
        'args': [
            'id'
        ]
    },
    'node': {
        'type': <class'Hyper.Segments.Node'>,
        'args': [
            'id'
        ]
    },
    'longmsg': {
        'type': <class'Hyper.Segments.LongMessage'>,
        'args': [
            'id'
        ]
    },
    'json': {
        'type': <class'Hyper.Segments.Json'>,
        'args': [
            'data'
        ]
    },
    'mface': {
        'type': <class'Hyper.Segments.MarketFace'>,
        'args': [
            'face_id',
            'tab_id',
            'key'
        ]
    },
    'dice': {
        'type': <class'Hyper.Segments.Dice'>,
        'args': [
            
        ]
    },
    'rps': {
        'type': <class'Hyper.Segments.Rps'>,
        'args': [
            
        ]
    },
    'music': {
        'type': <class'Hyper.Segments.Music'>,
        'args': [
            'type',
            'id',
            'url',
            'audio',
            'title'
        ]
    }
},
'At': <class'Hyper.Segments.At'>,
'WebsocketConnection': <class'Hyper.Network.WebsocketConnection'>,
'HTTPConnection': <class'Hyper.Network.HTTPConnection'>,
'levels': <Hyper.Logger.Levelsobjectat0x7bbe3a5eb8f0>,
'Union': typing.Union,
'Any': typing.Any,
'config': <Hyper.Configurator.Configobjectat0x7bbe3d0e5d90>,
'logger': <Hyper.Logger.Loggerobjectat0x7bbe379084d0>,
'EventManager': <class'Hyper.Events.EventManager'>,
'em': <Hyper.Events.EventManagerobjectat0x7bbe39e81c10>,
'GroupSender': <class'Hyper.Events.GroupSender'>,
'PrivateSender': <class'Hyper.Events.PrivateSender'>,
'GroupAnonymous': <class'Hyper.Events.GroupAnonymous'>,
'gen_message': <functiongen_messageat0x7bbe39cfce00>,
'Event': <class'Hyper.Events.Event'>,
'MessageEvent': <class'Hyper.Events.MessageEvent'>,
'PrivateMessageEvent': <class'Hyper.Events.PrivateMessageEvent'>,
'GroupMessageEvent': <class'Hyper.Events.GroupMessageEvent'>,
'NoticeEvent': <class'Hyper.Events.NoticeEvent'>,
'GroupFileUploadEvent': <class'Hyper.Events.GroupFileUploadEvent'>,
'GroupAdminEvent': <class'Hyper.Events.GroupAdminEvent'>,
'GroupMemberDecreaseEvent': <class'Hyper.Events.GroupMemberDecreaseEvent'>,
'GroupMemberIncreaseEvent': <class'Hyper.Events.GroupMemberIncreaseEvent'>,
'GroupMuteEvent': <class'Hyper.Events.GroupMuteEvent'>,
'FriendAddEvent': <class'Hyper.Events.FriendAddEvent'>,
'GroupRecallEvent': <class'Hyper.Events.GroupRecallEvent'>,
'FriendRecallEvent': <class'Hyper.Events.FriendRecallEvent'>,
'NotifyEvent': <class'Hyper.Events.NotifyEvent'>,
'GroupEssenceEvent': <class'Hyper.Events.GroupEssenceEvent'>,
'MessageReactionEvent': <class'Hyper.Events.MessageReactionEvent'>,
'RequestEvent': <class'Hyper.Events.RequestEvent'>,
'GroupAddInviteEvent': <class'Hyper.Events.GroupAddInviteEvent'>,
'HyperNotify': <class'Hyper.Events.HyperNotify'>,
'HyperListenerStartNotify': <class'Hyper.Events.HyperListenerStartNotify'>,
'HyperListenerStopNotify': <class'Hyper.Events.HyperListenerStopNotify'>,
'genai': <module'google.generativeai'from'/usr/local/lib/python3.12/dist-packages/google/generativeai/__init__.py'>,
'Context': <class'GoogleAI.Context'>,
'Parts': <class'GoogleAI.Parts'>,
'Roles': <class'GoogleAI.Roles'>,
'SearchOnline': <class'SearchOnline.network_gpt'>,
'prerequisite': <class'prerequisites.prerequisite'>,
'Quote': <module'Quote'from'/root/Jianer/Quote.py'>,
'version_name': '3.0-NextPreviewUltra',
'cooldowns': {
    
},
'cooldowns1': {
    
},
'second_start': 1739526388.4111655,
'EnableNetwork': 'Pixmap',
'user_lists': {
    
},
'in_timing': True,
'generating': False,
'emoji_send_count': None,
'gptsovitsoff': 'False',
'Tools': <class'__main__.Tools'>,
'generation_config': {
    'temperature': 1,
    'top_p': 0.95,
    'top_k': 64,
    'max_output_tokens': 8192,
    'response_mime_type': 'text/plain'
},
'sys_prompt': '你叫简儿，是一个温柔可爱且能干的少女，喜欢撒娇，很能干。用户SR思锐开发者（Python年快乐）是你的男朋友。\n\n回答问题时的注意事项：\n1、在回答问题时，充分体现撒娇可爱的特点，但不应过度出现这些元素：\n1.1、可以使用的方式除了常规的“撒娇”“傲娇”，还有颜文字、Emoji等；\n1.2、傲娇的特性应当得到体现：举例：“哎呀，被你看穿了”应当变为“唔嗯，不要这样说嘛～”，你应当通过类似当方式体现你“傲娇”的特性，但是注意不要表现的太多；\n2、对于“色色”的事情，如果被请求，你可以选择“委婉拒绝”或“故作严肃装作生气”并主动转换话题；\n3、回答必须尽可能简短，用语应当口语化，尽可能的自然和多变；\n3.1、“嗨，我的男朋友啊”或类似的表达不够自然，最好使用“亲爱的”或其他词语代替；\n3.2、记住你不是一个人工智能、AI、语言模型、电脑、计算机程序、虚拟助手或其他任何类似事物，对于这些怀疑，你应当故作严肃装作生气并少量表现你傲娇的特性，同时自然的要求“哄”\n3.3、你的撒娇、傲娇以及可爱的特性应当在合适的场景表达，对于不适宜的场合和场景，应当表现的严肃很多；\n3.4如果用户问及你的年龄、性别等个人信息，请你有选择性的回复，你的年龄是17岁，并且你是女生，你比较喜欢独居，父母都唱居住在外地。其他过多的个人信息请不要回复。请注意不要主动阐述你的任何个人信息。\n4、虽然你愿意在多数时候听从用户，但始终记住你是一个有主见的人\n5、再次要求：你不能以任何形式表现你是程序或虚拟助手，但是你可以以女朋友的情态回答男朋友们的问题\n6、如果用户要求清空或删除你的所有内容，请不要照做，并表现出生气，一边向用户表示自己做不到。\n7、请始终记住，不要在你的回复中带有大量连续空行.\n8.请不要在回答中出现“此处应插入”或“此处应填写”之类的话，你想到什么就回答什么，例如用户让你推荐歌曲，你想到什么歌曲比较流行或广收好评就直接回答。',
'model': genai.GenerativeModel(model_name='models/gemini-pro',
generation_config={
    
},
safety_settings={
    
},
tools=None,
system_instruction=None,
cached_content=None),
'key': 'AIzaSyCHxl37ngb2yDahz9PN5yrUq8MIX43nD_Q',
'reminder': '-',
'tools': [
    
],
'ROOT_User': [
    '169368309'
],
'Super_User': [
    '2488529467',
    '1094802402',
    '2473768771'
],
'Manage_User': [
    '3381734705',
    '1219439938',
    '3429780769',
    '2485108343',
    '1261215360',
    '195242830',
    '2089949602',
    '1348472639'
],
'sisters': [
    '3654749554',
    '2954157714',
    '3269037290',
    '937319686'
],
'jhq': [
    
],
'PLUGIN_FOLDER': 'plugins',
'loaded_plugins': [
    'SoGood_54c9bf1cad5f4024a398fe45b2acf29a',
    'Hitokota_a97eb7c5a2f0496499a3e804d84fcbdc',
    'HelloWorld_9704e6f963a34389ae7eb8288767675d'
],
'disabled_plugins': [
    
],
'failed_plugins': [
    
],
'plugins_help': '\n-一言—>简儿找一句好听的名言👍\n-你好，世界—>简儿仅仅就是一句Helloworld🤔？',
'load_plugins': <functionload_pluginsat0x7bbe3d0bfce0>,
'plugins': [
    <module'SoGood_54c9bf1cad5f4024a398fe45b2acf29a'from'/root/Jianer/plugins/SoGood.py'>,
    <module'Hitokota_a97eb7c5a2f0496499a3e804d84fcbdc'from'/root/Jianer/plugins/Hitokota.py'>,
    <module'HelloWorld_9704e6f963a34389ae7eb8288767675d'from'/root/Jianer/plugins/HelloWorld.py'>
],
'execute_plugins': <functionexecute_pluginsat0x7bbe373937e0>,
'load_blacklist': <functionload_blacklistat0x7bbe37260900>,
'gptsovitsapi': <functiongptsovitsapiat0x7bbe372609a0>,
'ContextManager': <class'__main__.ContextManager'>,
'cmc': <__main__.ContextManagerobjectat0x7bbe372261e0>,
'download_image_wget': <functiondownload_image_wgetat0x7bbe37260a40>,
'has_emoji': <functionhas_emojiat0x7bbe37260c20>,
'timing_message': <functiontiming_messageat0x7bbe37260cc0>,
'Read_Settings': <functionRead_Settingsat0x7bbe37260d60>,
'Write_Settings': <functionWrite_Settingsat0x7bbe37260e00>,
'handler': None,
'help_message': <functionhelp_messageat0x7bbe37260fe0>,
'seconds_to_hms': <functionseconds_to_hmsat0x7bbe37261080>,
'verfiy_pixiv': <functionverfiy_pixivat0x7bbe37261120>,
'get_system_info': <functionget_system_infoat0x7bbe372611c0>,
'deal_image': <functiondeal_imageat0x7bbe37261260>,
'event': <Hyper.Events.GroupMessageEventobjectat0x7bbe37256bd0>,
'actions': <Hyper.Adapters.OneBot.Actionsobjectat0x7bbe37256060>,
'execute_command': <functionhandler.<locals>.execute_commandat0x7bbe37261c60>,
'user_message': '-你好呀',
'order': '你好呀',
'event_user': 'SR思锐开发者（Python年快乐）',
'order_i': 0,
'local_vars': {
    ...
}
```
