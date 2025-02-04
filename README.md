# Jianer_QQ_bot

 OneBot v11，群管，AI，娱乐，新一代QQ群机器人。


## 功能

- 智能AI聊天(Google Gemini2 & ChatGPT 3.5 /4)
- 群管功能 冷静 撤回 自动审批
- 名言 将消息载入史册
- 生图 (ACG & P1x1v)
- 大头照
- 便携的交流方式 [见 [Preview](#preview)]


### Preview

QQ群: 983497968

## 部署

理论上全平台通用, 安装了 Python >= **3.9** 即可 (建议: **3.10+**)

1. Clone 本仓库 (建议先 Fork / Use this template)

```shell
git clone https://github.com/SRInternet-Studio/Jianer_QQ_bot.git
```

2. 安装依赖

```shell
pip install pyside6
pip install PySide6-Fluent-Widgets
pip install -r requirements.txt
```
国内服务器可使用清华源或者其他源 在后面加上
```shell
-i https://pypi.tuna.tsinghua.edu.cn/simple
```
3. 配置Bot
> **Linux(没有桌面)的用户可先在Win上启动配置程序,保存配置后将根目录下的"appsettings.json"和"config.json"复制到服务器即可**

先启动配置程序:

```shell
python SetupWizard.pyw
```

如果不出意外，会打开配置页面,将配置项目完成后,点击核对并应用设置,点击应用



## 使用
> **一定要先启动协议端(Lagrange),再启动主程序,不然会导致WARN 连接建立失败**
> **Linux用户可先在Win上启动配置程序,保存配置后将根目录下的"appsettings.json"和"config.json"复制到服务器即可**

启动协议端:
```shell
# Win
双击 Lagrange.OneBot.exe
# Linux
#先下载Lagrange Github地址:https://github.com/LagrangeDev/Lagrange.Core/releases/tag/nightly
#假设下载的文件名为lgr
chmod +x ./lgr
./lgr
#启动后均扫码登录即可
```
启动BOT主程序
```shell
python main.py
```
看到 ℹ️ INFO 成功建立连接 的日志，即表明与 OneBot实现对接成功。enjoy it!
## 关于

本项目框架 HypeR_Bot 由 HarcicYang [@HarcicYang Github](https://github.com/HarcicYang) 开发
HypeR_Bot Github地址:[@Github](https://github.com/HarcicYang/HypeR_Bot)
HypeR_Bot 官方文档:[@github.io](https://harcicyang.github.io/hyper-bot)
