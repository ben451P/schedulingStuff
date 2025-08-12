from utils import time_to_minutes

class Guard:
    def __init__(self, name, start, end):
        self.name = name
        self.start_time = time_to_minutes(start)
        self.end_time = time_to_minutes(end)
        self.lunch_break = False
        self.lunch_break_start = 0
        self.lunch_break_end = 0

        self.determine_if_lunch_break()

    def __repr__(self):
        return self.name
    
    def determine_if_lunch_break(self):
        self.lunch_break = self.end_time - self.start_time > 480

    def is_available_at(self, time: int) -> bool:
        on_shift = self.start_time <= time < self.end_time
        on_break = self.lunch_break_start <= time < self.lunch_break_end
        return on_shift and not on_break