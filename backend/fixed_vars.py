#these should be deleted later
from backend.station import Station
from backend.utils import time_to_minutes

ACCEPTABLE_LUNCH_START_TIME_RANGE = (time_to_minutes("13:00"), time_to_minutes("16:00"))

START = "11:00"
END = "19:30"

ROTATION_CYCLE = [
    "Kiddie", "Dive", "Main", "Break", "First Aid", "Slide",
    "Main2", "Rover", "Lap", "See Manager", "Bathroom Break"
]
STATION_IMPORTANCE_DESCENDING = [
    "Bathroom Break", "Rover", "Main2", "See Manager", "Slide",
    "Kiddie", "First Aid", "Dive", "Lap", "Main", "Break"
]

STATION_COVERAGE_TIMES = {
    i:[("11:00", "20:00")] for i in ROTATION_CYCLE
}

STATION_MAP = {
    i:Station(i,STATION_COVERAGE_TIMES[i]) for i in ROTATION_CYCLE
}

shifts = [
    ("Guard A1", "09:45", "15:30"),
    ("Guard B2", "09:45", "14:00"),
    ("Guard C3", "10:30", "16:00"),
    ("Guard D4", "10:30", "15:00"),
    ("Guard E5", "11:00", "16:00"),
    ("Guard E6", "11:00", "20:00"),
    ("Guard F7", "11:00", "20:00"),
    ("Guard G8", "11:00", "20:00"),
    ("Guard H9", "11:00", "20:00"),
    ("Guard K11", "15:00", "20:00"),
    ("Guard L12", "15:00", "20:00"),
    ("Guard L13", "15:00", "20:00"),
    ("Guard M14", "16:00", "20:00"),
    ("Guard M15", "16:00", "20:00"),
]