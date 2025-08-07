from datetime import datetime
import numpy as np
import pandas as pd
import csv

ROTATION_CYCLE = [
    "Kiddie", "Dive", "Main", "Break", "First Aid", "Slide",
    "Main2", "Rover", "Lap", "See Manager", "Bathroom Break"
]
STATION_IMPORTANCE_DESCENDING = [
    "Bathroom Break", "Rover", "Main2", "See Manager", "Slide",
    "Kiddie", "First Aid", "Dive", "Lap", "Main", "Break"
]

shifts = {
    "Guard A": ("09:45", "15:30"),
    "Guard B": ("09:45", "15:30"),
    "Guard C": ("10:30", "16:00"),
    "Guard D": ("10:30", "16:00"),
    "Guard E": ("11:00", "20:00"),
    "Guard F": ("11:00", "20:00"),
    # "Guard G": ("11:00", "20:00"),
    # "Guard H": ("11:00", "20:00"),
    "Guard I": ("13:00", "19:00"),
    "Guard J": ("14:00", "20:00"),
    "Guard K": ("14:00", "20:00"),
    "Guard L": ("14:00", "20:00"),
    "Guard M": ("15:30", "20:00"),
}

def time_to_minutes(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m

def minutes_to_time(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

class Guard:
    def __init__(self, name, start, end):
        self.name = name
        self.start_time = time_to_minutes(start)
        self.end_time = time_to_minutes(end)
        self.lunch_break = False
        self.lunch_hours = None

    def __repr__(self):
        return self.name

    def schedule_lunch(self):
        if self.end_time - self.start_time > 360:
            self.lunch_break = True

    def is_available_at(self, time: int) -> bool:
        return self.start_time <= time <= self.end_time

class Scheduler:
    def __init__(self, shifts):
        self.shifts = shifts
        self.guards = self.schedule_to_class()
        self.complete_schedule = False
        self.start = time_to_minutes("11:00")
        self.end = time_to_minutes("19:30")
        #schedule rows are time, cols are stations, in order of importance not actual rotation thing
        self.schedule = [[-1 for i in ROTATION_CYCLE] for _ in range(self.start,self.end,15)]

    def schedule_to_class(self):
        guards = []
        for name, (start, end) in self.shifts.items():
            guard = Guard(name, start, end)
            for g in range(len(guards)):
                if guards[g].name == guard.name:
                    guards[g].start_time = min(guards[g].start_time, guard.start_time)
                    guards[g].end_time = max(guards[g].end_time, guard.end_time)
                    break
            else:
                guards.append(guard)
        return guards
    


    def exchange_numbers(self,num1, num2, time):
        up_to = (time - self.start_time) / 15
        for j in range(up_to):
            for i in range(len(self.schedule[j])):
                if self.schedule[j][i] == num1:
                    self.schedule[j][i] = num2
                elif self.schedule[j][i] == num2:
                    self.schedule[j][i] = num1
        return self.schedule

    def available_guards(self, time_str):
        time = time_to_minutes(time_str)
        availability = [int(g.is_available_at(time)) for g in self.guards]
        # print(time_str, availability)
        return availability, availability.count(True)

    def schedule_lunches(self):
        #check when more guards will be coming onto shift during the alloted lunch break time
        #whenever guards come on, that many guards may leave. (later, exceptions should be coded in during camps and other stuff that may require more guards during certain times)
        #if we cant fit all the guards that need breaks into the alloted time, we start dropping stations in order of importance (later on avoiding the busy time)
        #iterate until all guards that need a break have one
        period = None
        influx = None
        drop = 0




    def create_base_schedule(self):
        time = time_to_minutes("11:00")

        prev_availability, prev_num_avail = self.available_guards(minutes_to_time(time))

        prev_state = []
        for i,j in enumerate(prev_availability):
            if j:prev_state.append(i+1)

        for row in range(len(self.schedule)):
            availability,num_avail = self.available_guards(minutes_to_time(time))

            #this is a rotation #####
            new_state = prev_state.copy()

            # temp = new_state.copy() + [-1] * (len(ROTATION_CYCLE) - len(new_state))
            # importance_index = {name: i for i, name in enumerate(STATION_IMPORTANCE_DESCENDING)}
            # reordered = [temp[importance_index[station]] for station in ROTATION_CYCLE]
            # reordered = reordered[:len(reordered) - reordered[::-1].index(-1) - 1]

            # temp = reordered[-1]
            # gap = 1
            # for i in range(1,len(reordered)):
            #     if reordered[i] == -1:
            #         gap += 1
            #     else:
            #         reordered[i] = reordered[i-gap]
            #         gap = 1
            # reordered[0] = temp
            
            # temp = reordered.copy() + [-1] * (len(ROTATION_CYCLE) - len(reordered))
            # cycle_index = {name: i for i, name in enumerate(ROTATION_CYCLE)}
            # original_order = [temp[cycle_index[station]] for station in STATION_IMPORTANCE_DESCENDING]

            # new_state = original_order[:len(original_order) - original_order[::-1].index(-1) - 1]
            # print(prev_state,"\n",new_state,"\n\n")
            new_state.append(new_state.pop(0))
            #up to here ####

            if prev_availability != availability:
                for i in range(len(availability)):
                    if not availability[i] and prev_availability[i]:
                        new_state[new_state.index(i)] = -1
                for i in range(len(availability)):
                    if availability[i] and not prev_availability[i]:
                        if -1 in new_state:
                            new_state[new_state.index(-1)] = i
                                    
            if num_avail > prev_num_avail:
                for guard_num in range(len(availability)):
                    if availability[guard_num] and guard_num not in new_state:
                        new_state.append(guard_num)

            elif num_avail < prev_num_avail:
                while -1 in new_state:
                    index = new_state.index(-1)
                    temp = new_state[index]
                    new_state[index] = new_state[-1]
                    new_state.pop(-1)


            self.schedule[row] = new_state + [-1] * (len(ROTATION_CYCLE) - len(new_state))

            time += 15
            prev_availability = availability.copy()
            prev_num_avail = num_avail
            prev_state = new_state.copy()
            
    def convert_to_csv(self):
        print(self.schedule)
        times = [minutes_to_time(t) for t in range(self.start, self.end, 15)]

        df = pd.DataFrame(
            self.schedule,
            index=times,
            columns=STATION_IMPORTANCE_DESCENDING[::-1]
        )

        df = df[ROTATION_CYCLE]

        df = df.T

        df.to_csv("schedule2.csv", index_label="Time")

        print("written")

    #main function
    def iterate_schedule(start,end,schedule):
        for i in range(len(schedule)):
            for j in range(len(schedule[i])):
                pass

scheduler = Scheduler(shifts)
scheduler.create_base_schedule()
scheduler.convert_to_csv()