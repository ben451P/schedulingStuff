from scheduler import Scheduler
from fixed_vars import shifts

if __name__ == "__main__":
    scheduler = Scheduler(shifts)
    scheduler.schedule_lunches()
    scheduler.create_base_schedule()
    scheduler.convert_to_excel()

    # be able to set a rotation start (3)
    # adjust rotation schedule to account for when certain stations wanna be closed (1)
    #handle when too many guards for stations by adding new "standby" stations lowest prioirty (4)
    #update anomly handler: whenever a station dissaperas, highligh number
