# HolidayCountdown.py
# 节日倒计时插件：列出未来两周的中国法定节假日（含调休），否则显示周末倒计时
# 支持每天早上8点自动推送到指定群

TRIGGHT_KEYWORD = "Any"
HELP_MESSAGE = "-倒计时 / -节日倒计时 / -下个节日 —— 显示未来两周的中国法定节假日倒计时（含调休），无显示周末倒计时"

import sys, subprocess, datetime, asyncio

# 自动安装 chinese-calendar
try:
    import chinese_calendar as cc
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "chinese-calendar"])
    import chinese_calendar as cc


def get_future_holidays_within(start_date: datetime.date, days_ahead: int = 14):
    """获取未来 days_ahead 天内的假期（含调休），返回列表 [(date, name), ...]"""
    result = []
    for i in range(0, days_ahead + 1):
        d = start_date + datetime.timedelta(days=i)
        if cc.is_holiday(d):
            name = cc.get_holiday_detail(d)[0] or "假期"
            result.append((d, name))
    return result


def find_next_weekend(start_date: datetime.date):
    """返回下一个周末（优先周六），(date, which, days_until)"""
    for delta in range(0, 14):
        d = start_date + datetime.timedelta(days=delta)
        if d.weekday() == 5:
            return d, "周六", delta
        if d.weekday() == 6:
            return d, "周日", delta
    return start_date + datetime.timedelta(days=7), "周六", 7


def format_holiday_list(holidays, today):
    lines = ["🎯 未来两周假期（含调休）:"]
    for d, name in holidays:
        days = (d - today).days
        when = "今天 🎉" if days == 0 else ("明天" if days == 1 else f"{days}天后")
        lines.append(f"📅 {d.isoformat()} {name}  ⏳ {when}")
    return "\n".join(lines)


def format_weekend_reply(d, which, days):
    if days == 0:
        when = "今天就是周末 🎉"
    elif days == 1:
        when = "明天就是周末"
    else:
        when = f"还有 {days} 天到 {which}"
    return f"🏖️ 未来两周无假期，显示最近周末：{which}\n📅 {d.isoformat()}\n⏳ {when}"


async def send_countdown(actions, Manager, Segments, group_id: int):
    """构建并发送倒计时消息"""
    today = datetime.date.today()
    holidays = get_future_holidays_within(today, 14)
    if holidays:
        reply = format_holiday_list(holidays, today)
    else:
        d, which, days = find_next_weekend(today)
        reply = format_weekend_reply(d, which, days)

    await actions.send(group_id=group_id, message=Manager.Message(Segments.Text(reply)))


async def on_message(event, actions, Manager, Segments, Events, **kwargs):
    order = kwargs.get("order", "")
    triggers = ["倒计时", "节日倒计时", "下个节日", "下一个节日"]
    if not any(t in order for t in triggers):
        return False

    await send_countdown(actions, Manager, Segments, getattr(event, "group_id", None))
    return True


# ================= 定时任务部分 =================

async def daily_scheduler(actions, Manager, Segments):
    """每天 8:00 推送到指定群"""
    group_id = 310444809  # 目标群号
    while True:
        now = datetime.datetime.now()
        # 下一次执行的时间
        next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += datetime.timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        try:
            await send_countdown(actions, Manager, Segments, group_id)
        except Exception as e:
            print(f"[HolidayCountdown] 定时任务发送失败：{e}")


async def on_startup(actions, Manager, Segments, Events, **kwargs):
    """插件加载时启动定时任务"""
    asyncio.create_task(daily_scheduler(actions, Manager, Segments))