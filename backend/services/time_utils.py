import random
import re
from typing import Optional, Tuple

TIME_RANGE_SEPARATOR = re.compile(r"\s*[-–—to]+\s*", flags=re.IGNORECASE)


def parse_time_value(value: str) -> Optional[int]:
    if not value:
        return None

    cleaned = value.strip().lower()
    if not cleaned:
        return None

    parts = cleaned.split(":")
    try:
        hour = int(parts[0])
    except ValueError:
        return None

    minute = 0
    if len(parts) > 1:
        try:
            minute = int(parts[1])
        except ValueError:
            return None

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None

    return hour * 60 + minute


def parse_time_range(time_str: str) -> Tuple[Optional[int], Optional[int]]:
    if not time_str or not isinstance(time_str, str):
        return None, None

    parts = TIME_RANGE_SEPARATOR.split(time_str.strip())
    if len(parts) == 0:
        return None, None

    start = parse_time_value(parts[0])
    end = None
    if len(parts) > 1:
        end = parse_time_value(parts[1])

    return start, end


def format_minutes(minutes: int) -> str:
    if minutes is None or not isinstance(minutes, int):
        return ""

    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def times_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    if start_a is None or end_a is None or start_b is None or end_b is None:
        return False
    return start_a < end_b and start_b < end_a


def get_random_class_duration(start_min: Optional[int] = None) -> int:
    duration = 120 if random.random() < 0.75 else 60
    if start_min is None:
        return duration

    if start_min + duration > 20 * 60:
        if start_min + 60 <= 20 * 60:
            return 60
        return max(60, 20 * 60 - start_min)

    return duration
