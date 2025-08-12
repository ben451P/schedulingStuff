from backend.utils import minutes_to_time, time_to_minutes
from backend.guard import Guard
from backend.station import Station

class Scheduler:
    def __init__(self, start, end, lunch_start, lunch_end, rotation_cycle, importance_order, coverage_times, shifts):
        self.shifts = shifts
        self.guards = self.schedule_to_class()
        self.complete_schedule = False

        self.start = time_to_minutes(start)
        self.end = time_to_minutes(end)
        self.lunch_start = time_to_minutes(lunch_start)
        self.lunch_end = time_to_minutes(lunch_end)

        self.rotation_cycle = rotation_cycle
        self.station_importance_descending = importance_order
        self.coverage_times = coverage_times

        #schedule rows are time, cols are stations, in order of importance not actual rotation thing
        self.schedule = [[-1 for _ in self.rotation_cycle] for _ in range(self.start,self.end,15)]

        self.station_map = {i:Station(i,self.coverage_times[i]) for i in self.rotation_cycle}

    def schedule_to_class(self):
        guards = []
        for name, start, end in self.shifts:
            guard = Guard(name, start, end)
            for g in range(len(guards)):
                if guards[g].name == guard.name:
                    guards[g].start_time = min(guards[g].start_time, guard.start_time)
                    guards[g].end_time = max(guards[g].end_time, guard.end_time)
                    guards[g].determine_if_lunch_break()
                    break
            else:
                guards.append(guard)
        return guards
    
    def manually_override_lunches(self, lunches):
        for i in range(len(self.guards)):
            if not self.guards[i].start_time == self.guards[i].end_time:
                self.guards[i].lunch_break = lunches[i]


    def available_guards(self, time_str):
        time = time_to_minutes(time_str)
        availability = [int(g.is_available_at(time)) for g in self.guards]
        return availability, availability.count(True)
    
    def needed_stations(self,time):
        needed = [0 for _ in range(len(self.station_importance_descending))]
        for j, i in enumerate(self.station_importance_descending):
            station = self.station_map[i]
            for t in range(time,time + 60, 15):
                if station.should_be_open_at(t):
                    needed[j] = 1
                    break
                
        return needed, needed.count(1)

    def schedule_lunches(self):
    
        period_start, period_end = self.lunch_start, self.lunch_end
        drop = 0
        finished_scheduling = False

        needed_lunch_breaks = [guard.lunch_break for guard in self.guards]

        while not finished_scheduling:
            check = needed_lunch_breaks.copy()
            temp_guards_on_break = []
            for time in range(period_start,period_end, 15):
                avail_guards, num_avail_guards = self.available_guards(minutes_to_time(time))
                needed_stats, num_needed_stats = self.needed_stations(time)

                difference = num_needed_stats - num_avail_guards - drop + len(temp_guards_on_break)

                #need to correct for assumption that least important station is gonna go
                while difference < 0:
                    #give lunch breaks while there is a difference
                    if True in check:
                        index = check.index(True)
                        check[index] = time
                        temp_guards_on_break.append(4)
                    difference += 1
                #increment for looop
                pointer = 0
                while pointer < len(temp_guards_on_break):
                    temp_guards_on_break[pointer] -= 1
                    if temp_guards_on_break[pointer] == 0:
                        temp_guards_on_break.pop(pointer)
                    else:pointer += 1

            if True not in check:
                finished_scheduling = True
            # check if everyones break is scheduled
            drop += 1
        
        #updating the actual info
        for i in range(len(self.guards)):
            if check[i]:
                self.guards[i].lunch_break_start = check[i]
                self.guards[i].lunch_break_end = check[i] + 60

    def add_fodder_station(self, index):
        count = 1
        for i in self.rotation_cycle:
            if "Standby" in i:
                count += 1
        station_name = "Standby" + str(count)

        self.station_importance_descending.insert(0,station_name)
        self.rotation_cycle.append(station_name)

        for i in range(index):
            self.schedule[i].append(-1)

    def create_base_schedule(self):
        time = self.start

        prev_availability, prev_num_avail = self.available_guards(minutes_to_time(time))

        prev_state = []
        for i,j in enumerate(prev_availability):
            if j:prev_state.append(i)

        for row in range(len(self.schedule)):
            availability,num_avail = self.available_guards(minutes_to_time(time))

            if num_avail > len(self.schedule[row]):
                self.add_fodder_station(row)

            #does default rotation unless new, less or different guards than before
            new_state = prev_state.copy()
            if prev_availability != availability:
                for i in range(len(availability)):
                    #if guard is leaving mark station as unattended
                    if not availability[i] and prev_availability[i]:
                        new_state[new_state.index(i)] = -1
                #if different guards, find an unattended station and man it
                for i in range(len(availability)):
                    if availability[i] and not prev_availability[i]:
                        if -1 in new_state:
                            new_state[new_state.index(-1)] = i
                
            #if more guards than before, open next most impotant station
            if num_avail > prev_num_avail:
                for guard_num in range(len(availability)):
                    if availability[guard_num] and guard_num not in new_state:
                        new_state.append(guard_num)

            #if less guards, shift so that least important station is unattended
            elif num_avail < prev_num_avail:
                while -1 in new_state:
                    index = new_state.index(-1)
                    temp = new_state[index]
                    new_state[index] = new_state[-1]
                    new_state.pop(-1)

            #this is a rotation #####
            temp = new_state.copy() + [-1] * (len(self.rotation_cycle) - len(new_state))
            importance_index = {name: i for i, name in enumerate(self.station_importance_descending[::-1])}
            reordered = [temp[importance_index[station]] for station in self.rotation_cycle]
            while reordered and reordered[-1] == -1:
                reordered.pop(-1)

            front_negs = 0
            while reordered and reordered[0] == -1:
                reordered.pop(0)
                front_negs += 1
            temp = reordered[-1]
            gap = 1
            pointer = len(reordered) - 1
            # Remove temp from its current position before rotation
            while pointer > 0:
                if reordered[pointer - gap] == -1:
                    gap += 1
                else:
                    reordered[pointer] = reordered[pointer - gap]
                    pointer -= gap
                    gap = 1
            reordered[0] = temp

            reordered = [-1] * front_negs + reordered

            temp = reordered.copy() + [-1] * (len(self.rotation_cycle) - len(reordered))
            cycle_index = {name: i for i, name in enumerate(self.rotation_cycle)}
            original_order = [temp[cycle_index[station]] for station in self.station_importance_descending[::-1]]
            while original_order and original_order[-1] == -1:
                original_order.pop(-1)
            
            new_state = original_order.copy()
            #up to here ####

            self.schedule[row] = new_state + [-1] * (len(self.rotation_cycle) - len(new_state))

            time += 15
            prev_availability = availability.copy()
            prev_num_avail = num_avail
            prev_state = new_state.copy()
        
        for i in range(len(self.schedule)):
            for j in range(len(self.schedule[i])):
                if self.schedule[i][j] != -1:
                    self.schedule[i][j] += 1
                    

    