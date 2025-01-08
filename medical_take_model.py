import pandas as pd
import simpy
import random

from class_def import g 
from class_def import Patient 

class Model: 

# constructor

  def __init__(self, run_number):
    self.env = simpy.Environment()
    self.patient_counter = 0 # used as a patient ID

    # resources
    self.nurse = simpy.Resource (self.env, 
        capacity = g.number_of_nurses)
    self.sdec_doctor = simpy.Resource (self.env, 
        capacity = g.number_of_sdec_doctors)
    self.take_doctor = simpy.Resource (self.env, 
        capacity = g.number_of_take_doctors)
    self.acute_consultant = simpy.Resource (self.env, 
        capacity = g.number_of_acute_consultants)
    self.sdec_consultant = simpy.Resource (self.env, 
        capacity = g.number_of_sdec_consultants)
    self.pod_consultant = simpy.Resource (self.env, 
        capacity = g.number_of_pod_consultants)
    self.cardio_consultant = simpy.Resource (self.env, 
        capacity = g.number_of_cardio_consultants)
    self.run_number = run_number 
    self.results_df = pd.DataFrame (columns= [
        "Patient ID", "Patient Route", "Q Time Nurse", "Time with Nurse",
        "Q Time Doctor", "Time with Doctor","Time for Ix",
        "Q Time Consultant", "Time with Consultant", 
        "Disposition Time", "Patient Disposition", 
        "Total Journey Time"])
    self.results_df.set_index("Patient ID", inplace=True)

    self.mean_q_time_nurse = 0
    self.mean_q_time_doctor = 0
    self.mean_q_time_consultant = 0

# generator - patient arrives at hospital

def generator_patient_arrival (self):
        while True:
            self.patient_counter += 1
            p = Patient (self.patient_counter)
            p.start_time = self.env.now 
            self.env.process (self.attend_hospital (p))

            #print(f"Generating Patient {self.patient_counter} at time {self.env.now}")

            #randomly sample time to patient arrival
            sampled_inter = random.expovariate (1.0/ g.sdec_patient_inter)
            yield self.env.timeout (sampled_inter)


# patient sent along 1 of 3 pathways - SDEC, med expect in ED, ED referal 
# pathways involve triage, clerking and review by a consultant, with some 
# patients being discharged along the way

def attend_hospital (self, patient):

        patient_route = "SDEC"