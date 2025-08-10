from datetime import datetime
import numpy as np
import pandas as pd
import csv

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

shifts = {
    "Guard A": ("09:45", "15:30"),
    "Guard B": ("09:45", "15:30"),
    "Guard C": ("10:30", "16:00"),
    "Guard D": ("10:30", "16:00"),
    "Guard E": ("11:00", "20:00"),
    "Guard F": ("11:00", "20:00"),
    "Guard G": ("11:00", "20:00"),
    "Guard H": ("11:00", "20:00"),
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

ACCEPTABLE_LUNCH_START_TIME_RANGE = (time_to_minutes("13:00"), time_to_minutes("16:00"))

class Guard:
    def __init__(self, name, start, end):
        self.name = name
        self.start_time = time_to_minutes(start)
        self.end_time = time_to_minutes(end)
        self.lunch_break = self.end_time - self.start_time > 360
        self.lunch_break_start = 0
        self.lunch_break_end = 0

    def __repr__(self):
        return self.name

    def is_available_at(self, time: int) -> bool:
        on_shift = self.start_time <= time < self.end_time
        on_break = self.lunch_break_start <= time < self.lunch_break_end
        return on_shift and not on_break

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
    
    def needed_stations(self,time):
        needed = [0 for _ in range(len(STATION_IMPORTANCE_DESCENDING))]
        for j, i in enumerate(STATION_IMPORTANCE_DESCENDING):
            station = STATION_MAP[i]
            for t in range(time,time + 60, 15):
                if station.should_be_open_at(t):
                    needed[j] = 1
                    break
                
        return needed, needed.count(1)

    def schedule_lunches(self):
        #check when more guards will be coming onto shift during the alloted lunch break time
        #whenever guards come on, that many guards may leave. (later, exceptions should be coded in during camps and other stuff that may require more guards during certain times)
        #if we cant fit all the guards that need breaks into the alloted time, we start dropping stations in order of importance (later on avoiding the busy time)
        #iterate until all guards that need a break have one
        period_start, period_end = ACCEPTABLE_LUNCH_START_TIME_RANGE
        influx = 0
        drop = 0
        finished_scheduling = False

        # lunch_break_periods = (period_end - period_start) % 60
        needed_lunch_breaks = [guard.lunch_break for guard in self.guards]

        

        while not finished_scheduling:
            check = needed_lunch_breaks.copy()
            for time in range(period_start,period_end, 15):
                avail_guards, num_avail_guards = self.available_guards(minutes_to_time(time))
                needed_stats, num_needed_stats = self.needed_stations(time)
                print(num_needed_stats, num_avail_guards, drop)

                difference = num_needed_stats - num_avail_guards - drop

                #need to correct for assumption that least important station is gonna go
                while difference < 0:
                    #give lunch breaks while there is a difference
                    if True in check:
                        index = check.index(True)
                        check[index] = time
                    difference += 1
                #increment for looop
            if True not in check:
                finished_scheduling = True
            # check if everyones break is scheduled
            drop += 1
        
        #updating the actual info
        for i in range(len(self.guards)):
            if check[i]:
                self.guards[i].lunch_break_start = check[i]
                self.guards[i].lunch_break_end = check[i] + 60
                    

    def create_base_schedule(self):
        time = time_to_minutes("11:00")

        prev_availability, prev_num_avail = self.available_guards(minutes_to_time(time))

        prev_state = []
        for i,j in enumerate(prev_availability):
            if j:prev_state.append(i)

        for row in range(len(self.schedule)):
            availability,num_avail = self.available_guards(minutes_to_time(time))

            #this is a rotation #####
            new_state = prev_state.copy()

            temp = new_state.copy() + [-1] * (len(ROTATION_CYCLE) - len(new_state))
            importance_index = {name: i for i, name in enumerate(STATION_IMPORTANCE_DESCENDING[::-1])}
            reordered = [temp[importance_index[station]] for station in ROTATION_CYCLE]
            while reordered and reordered[-1] == -1:
                reordered.pop(-1)

            temp = reordered[-1]
            gap = 1
            pointer = len(reordered) - 1
            while pointer > 0:
                if reordered[pointer - gap] == -1:
                    gap += 1
                else:
                    reordered[pointer] = reordered[pointer - gap]
                    pointer -= gap
                    gap = 1
            reordered[0] = temp

            temp = reordered.copy() + [-1] * (len(ROTATION_CYCLE) - len(reordered))
            cycle_index = {name: i for i, name in enumerate(ROTATION_CYCLE)}
            original_order = [temp[cycle_index[station]] for station in STATION_IMPORTANCE_DESCENDING[::-1]]
            while original_order and original_order[-1] == -1:
                original_order.pop(-1)
            
            new_state = original_order.copy()
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
        for guard in self.guards:
            print(guard.lunch_break_start,guard.lunch_break_end)

        times = [minutes_to_time(t) for t in range(self.start, self.end, 15)]

        df = pd.DataFrame(
            self.schedule,
            index=times,
            columns=STATION_IMPORTANCE_DESCENDING[::-1]
        )

        df = df[ROTATION_CYCLE]

        df = df.T

        df.to_csv("schedule3.csv", index_label="Time")

        print("written")

    #main function
    def iterate_schedule(start,end,schedule):
        for i in range(len(schedule)):
            for j in range(len(schedule[i])):
                pass

scheduler = Scheduler(shifts)
scheduler.schedule_lunches()
scheduler.create_base_schedule()
scheduler.convert_to_csv()
