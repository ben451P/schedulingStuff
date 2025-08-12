from .utils import time_to_minutes

class Station:
    def __init__(self, name, times_when_open: list):
        self.name = name
        self.times_when_open = times_when_open #list with tuples (start_time,end_time)

    def __repr__(self):
        return self.name
    
    def should_be_open_at(self,time):
        for item in self.times_when_open:
            if time_to_minutes(item[0]) <= time < time_to_minutes(item[1]):
                return True
        return False