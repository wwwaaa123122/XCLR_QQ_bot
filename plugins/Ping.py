import asyncio
import sys
import re
import json
import socket
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

TRIGGHT_KEYWORD = "ping "  # 关键字后需跟目标域名或IP（注意末尾空格）
HELP_MESSAGE = "- ping <域名或IP> —> 对目标执行4次ping，并返回IP地理位置信息"

# ------- 工具函数 -------

async def _run_ping(host: str) -> str:
    is_windows = sys.platform.startswith("win")
    if is_windows:
        cmd = ["ping", "-n", "4", host]
    else:
        cmd = ["ping", "-c", "4", "-W", "2", host]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        return out.decode(errors="ignore")
    except Exception as e:
        return f"[ping 执行失败] {e!r}"

def _extract_latencies_ms(ping_text: str):
    times = []
    for m in re.finditer(r"[Tt]ime[=<]?\s*=?\s*([\d\.]+)\s*ms", ping_text):
        try:
            times.append(float(m.group(1)))
        except:
            pass
    if not times:
        for m in re.finditer(r"时间[=<]?\s*=?\s*([\d\.]+)\s*ms", ping_text):
            try:
                times.append(float(m.group(1)))
            except:
                pass
    return times[:4]

def _extract_packet_loss(ping_text: str):
    m = re.search(r"(\d+)\s*%\s*packet\s*loss", ping_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"\(\s*(\d+)\s*%\s*loss\s*\)", ping_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"丢失\s*=\s*\d+\s*\(\s*(\d+)\s*%\s*丢失", ping_text)
    if m:
        return int(m.group(1))
    return None

def _resolve_ip(host: str) -> str:
    try:
        socket.inet_pton(socket.AF_INET, host)
        return host
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return host
    except OSError:
        pass
    info = socket.getaddrinfo(host, None)
    if not info:
        raise RuntimeError("DNS 解析失败")
    return info[0][4][0]

async def _fetch_geo(ip: str) -> dict:
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,org,as,query,timezone,lat,lon"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    loop = asyncio.get_running_loop()
    try:
        data = await loop.run_in_executor(
            None,
            lambda: urlopen(req, timeout=8).read().decode("utf-8", errors="ignore"),
        )
        j = json.loads(data)
        if j.get("status") != "success":
            return {"error": j.get("message", "geo lookup failed")}
        return j
    except (URLError, HTTPError, TimeoutError) as e:
        return {"error": f"geo request failed: {e}"}
    except Exception as e:
        return {"error": f"geo unexpected error: {e}"}

def _fmt_geo(geo: dict) -> str:
    if not geo or "error" in geo:
        return f"地理位置：查询失败（{geo.get('error','unknown')}）"
    parts = []
    country = geo.get("country")
    region = geo.get("regionName")
    city = geo.get("city")
    isp = geo.get("isp")
    asn = geo.get("as")
    tz = geo.get("timezone")
    lat = geo.get("lat")
    lon = geo.get("lon")
    loc = " / ".join([p for p in [country, region, city] if p])
    if loc:
        parts.append(f"地理位置：{loc}")
    if isp:
        parts.append(f"ISP：{isp}")
    if asn:
        parts.append(f"AS：{asn}")
    if tz:
        parts.append(f"时区：{tz}")
    if lat is not None and lon is not None:
        parts.append(f"坐标：{lat},{lon}")
    return "\n".join(parts) if parts else "地理位置：未知"

# ------- 插件主入口 -------

async def on_message(event, actions, Manager, Segments):
    try:
        text = str(getattr(event, "message", "")).strip()
    except Exception:
        text = ""

    idx = text.lower().find(TRIGGHT_KEYWORD)
    if idx == -1:
        return

    target = text[idx + len(TRIGGHT_KEYWORD):].strip()
    if not target:
        reply = "用法：ping <域名或IP>\n示例：ping 1.1.1.1"
        await actions.send(group_id=getattr(event, "group_id", None),
                           message=Manager.Message(Segments.Text(reply)))
        return True

    try:
        ip = await asyncio.get_running_loop().run_in_executor(None, _resolve_ip, target)
    except Exception as e:
        reply = f"目标：{target}\nDNS 解析失败：{e}"
        await actions.send(group_id=getattr(event, "group_id", None),
                           message=Manager.Message(Segments.Text(reply)))
        return True

    ping_task = asyncio.create_task(_run_ping(ip))
    geo_task = asyncio.create_task(_fetch_geo(ip))
    ping_text, geo = await asyncio.gather(ping_task, geo_task)

    times = _extract_latencies_ms(ping_text)
    loss = _extract_packet_loss(ping_text)

    if times:
        avg = sum(times) / len(times)
        times_line = "、".join(f"{t:.1f}ms" for t in times)
    else:
        avg = None
        times_line = "未解析到延迟值"

    lines = [
        f"目标：{target}",
        f"解析IP：{ip}",
        _fmt_geo(geo),
        f"4次延迟：{times_line}",
        f"平均延迟：{avg:.1f}ms" if avg is not None else "平均延迟：未知",
        f"丢包率：{loss}%" if loss is not None else "丢包率：未知",
    ]

    msg = "\n".join(lines)
    await actions.send(
        group_id=getattr(event, "group_id", None),
        message=Manager.Message(Segments.Text(msg))
    )
    return True