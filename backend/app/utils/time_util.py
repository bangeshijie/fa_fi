"""项目统一的北京时间工具。"""

from datetime import datetime
from zoneinfo import ZoneInfo


BEIJING_TIMEZONE = ZoneInfo("Asia/Shanghai")


def now_beijing() -> datetime:
    """返回带东八区时区信息的当前时间。"""
    return datetime.now(BEIJING_TIMEZONE)


def now_beijing_naive() -> datetime:
    """返回东八区当前时间，但移除时区信息以兼容旧的 timestamp 字段。"""
    return now_beijing().replace(tzinfo=None)
