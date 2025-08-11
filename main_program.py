from scheduler import Scheduler
from fixed_vars import shifts

if __name__ == "__main__":
    scheduler = Scheduler(shifts)
    scheduler.schedule_lunches()
    scheduler.create_base_schedule()
    scheduler.convert_to_excel()

    # be able to set a rotation start (3)
    # add another station of see manager (5)
    # adjust rotation schedule to account for when certain stations wanna be closed (1)
    #finish front end (5)
    # be able to manually take away lunch breaks (do in front end)
    #handle when too many guards for stations by adding new "standby" stations lowest prioirty (4)