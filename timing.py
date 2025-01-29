# copied and modified from src/helper.py
# credit to Thomas Knight 
# https://github.com/tomwhknight/emergency_care_simulation/blob/main/src/helper.py

import datetime
import numpy as np
import math

def calculate_hour_of_day(simulation_time):
    """Converts the simulation time (in minutes) to a readable time of day (HH:MM)."""
    total_minutes = int(simulation_time % 1440)  # Get remainder of time in current day
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02}:{minutes:02}"  # Format time as HH:MM

def calculate_day_of_week(simulation_time):
    """Calculates the day of the week based on simulation time (assuming day 0 is Monday)."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_of_week = int(simulation_time // 1440) % 7  # Divide by 1440 (minutes in a day)
    return days[day_of_week]

def extract_hour(simulation_time):
    """Extracts the hour of the day as an integer from the simulation time (in minutes)."""
    total_minutes = int(simulation_time % 1440)  # Get remainder of time in the current day
    return total_minutes // 60  # Return only the hour as an integer

def get_doctor_patient_count(self, doctor_type):
    return self.doctor_patient_counter.get(doctor_type, 0)

def get_consultant_patient_count(self, consultant_type):
    return self.consultant_patient_counter.get(consultant_type, 0)



'''def calc_hour_of_day (simulation_time):

    # converts simulation time (in minutes) to hours of the day 


def obstruct_cardiologist(self):
    while True:

        hour_of_day = extract_hour (self.env.now)

        if hour_of_day > g.cardio_start: 
            with self.cardio_consultant.request(priority=-1) as req:
                yield req  # Block the resource
                print (f"The patient {patient_id} has been added to the cardio PTWR list. The cardiologists start ward round at 0900")
                yield self.env.timeout(60)  # Hold the block for 1 hour
                
        else:
            print(f"Patient {patient_id} will be seen on the cardio PTWR")

        # Wait until the next hour to check again
        yield self.env.timeout(60)
        
def obstruct_medical_consultant(self):
    while True:

        hour_of_day = extract_hour (self.env.now)

        if g.med_cons_start <= hour_of_day < g.med cons_finish:
            with self.consultant.request(priority=-1) as req:
                yield req  # Block the resource
                print (f"The patient {patient_id} has been added to the cardio PTWR list. The cardiologists start ward round at 0900")
                yield self.env.timeout(60)  # Hold the block for 1 hour
                
        else:
            print(f"Patient {patient_id} will be seen on the cardio PTWR")

        # Wait until the next hour to check again
        yield self.env.timeout(60)

def obstruct_sdec_consultant(self):
    while True:

        hour_of_day = extract_hour (self.env.now)

        if hour_of_day > g.cardio_start: 
            with self.consultant.request(priority=-1) as req:
                yield req  # Block the resource
                print (f"The patient {patient_id} has been added to the cardio PTWR list. The cardiologists start ward round at 0900")
                yield self.env.timeout(60)  # Hold the block for 1 hour
                
        else:
            print(f"Patient {patient_id} will be seen on the cardio PTWR")

        # Wait until the next hour to check again
        yield self.env.timeout(60)

def obstruct_acute_med_consultant(self):
    while True:

        hour_of_day = extract_hour (self.env.now)

        if hour_of_day > g.cardio_start: 
            with self.consultant.request(priority=-1) as req:
                yield req  # Block the resource
                print (f"")
                yield self.env.timeout(60)  # Hold the block for 1 hour
                
        else:
            print(f"Patient {patient_id} will be seen on the cardio PTWR")

        # Wait until the next hour to check again
        yield self.env.timeout(60)



        # The generator first pauses for the frequency period
        yield self.env.timeout(g.)

        # Once elapsed, the generator requests (demands?) a nurse with
        # a priority of -1.  This ensure it takes priority over any patients
        # (whose priority values start at 1).  But it also means that the
        # nurse won't go on a break until they've finished with the current
        # patient
        with self.cardio_consultant.request(priority=-1) as req:
            yield req

            print (f"{self.env.now:.2f}: The nurse is now on a break and will be back at",
                    f"{(self.env.now + g.unav_time_nurse):.2f}")

            # Freeze with the nurse held in place for the unavailability
            # time (ie duration of the nurse's break).  Here, both the
            # duration and frequency are fixed, but you could randomly
            # sample them from a distribution too if preferred.
            yield self.env.timeout(g.unav_time_nurse)

 # Method to model restricted consultant working hours 
    def obstruct_consultant(self):
        """Simulate consultant unavailability between 21:00 and 07:00."""
        while True:
            # Extract the current hour
            current_hour = extract_hour(self.env.now)

            # Check if the current time is within the off-duty period (21:00–07:00)
            if current_hour >= 21 or current_hour < 7:
                print(f"{self.env.now:.2f}: Consultants are off-duty (21:00–07:00).")
                with self.consultant.request(priority=-1) as req:
                    yield req  # Block the resource
                    yield self.env.timeout(60)  # Hold the block for 1 hour
            else:
                print(f"{self.env.now:.2f}: Consultants are available.")

            # Wait until the next hour to check again
            yield self.env.timeout(60)
    '''