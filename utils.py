from datetime import datetime


def time_to_minutes(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m

def minutes_to_time(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def military_to_normal(time):
    dt = datetime.strptime(time, "%H:%M")
    result = dt.strftime("%I:%M").lstrip("0")
    return result
