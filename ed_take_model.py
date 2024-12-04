import pandas as pd
import simpy
import random

from class_def import g 
from class_def import Patient

# model

 # constructor 
    def __init__(self, run_number):
        self.env = simpy.Environment()
        self.patient_counter = 0 # used as a patient ID

        # resources
        self.doctor = simpy.Resource (self.env, 
            capacity = g.number_of_doctors)
        self.medical_consultant = simpy.Resource (self.env, 
            capacity = g.number_of_consultants)
        self.cardio_consultant = simpy.Resource (self.env, 
            capacity = g.number_of_cardio_consultants)
        self.run_number = run_number 
        #self.results_df = pd.DataFrame (columns= [
           # "Patient ID", "Q Time Nurse", "Time with Nurse",
           # "Q Time Doctor", "Time with Doctor",
           # "Q Time Consultant", "Time with Consultant", "Total Journey Time"])

        self.results_df = pd.DataFrame()
        self.results_df["Patient ID"] = [1]
        #self.results_df["Patient Route"] = []
        self.results_df["Q Time Doctor"] = [0.0]
        self.results_df["Time with Doctor"] = [0.0]
        self.results_df["Time for Ix"] = [0.0]
        self.results_df["Q Time Consultant"] = [0.0]
        self.results_df["Time with Consultant"] = [0.0]
        self.results_df["Total Journey Time"] = [0.0]
        self.results_df.set_index("Patient ID", inplace=True)

        self.mean_q_time_nurse = 0
        self.mean_q_time_doctor = 0
        self.mean_q_time_consultant = 0

    # generator function to arrive at hospital
    def generator_patient_arrival (self):
        while True:
            self.patient_counter += 1 
            p = Patient (self.patient_counter)
            p.start_time = self.env.now 
            self.env.process (self.ed_medical_take (p))
            #randomly sample time to patient arrival
            sampled_inter = random.expovariate (1.0/ g.patient_inter)
            yield self.env.timeout (sampled_inter)
    
    # generator function to pass through medical take 
    def ed_medical_take (self, patient):

        # log that patient attended ED into Patient Route 

        # doctor process 
        start_q_doctor = self.env.now
        with self.doctor.request() as req:
            yield req
            end_q_doctor = self.env.now
            # need to consider changing this to log normal
            patient.q_time_doctor = end_q_doctor - start_q_doctor
            sampled_doctor_time = random.expovariate (1.0/ g.mean_doctor_time)
            yield self.env.timeout(sampled_doctor_time)

            # Need to add in discharge probability here 

            # Assign PTWR status here - cardio vs medical
            if random.random() < prob_needs_cardioptwr:  # Probability of 0.1 for cardio
                patient.flow = "cardio"
                return patient.flow 
            else:
                patient.flow = "medical"
                return patient.flow

        # investigation sink
        ix_time = random.expovariate(1.0 / mean_ed_ix_time)
        patient.ix_time = ix_time
        yield self.env.timeout(ix_time)

        # PTWR process 
        # Can either see a cardiology consultant or a medical consultant

        if  patient.flow == "cardio":

            # cardio PTWR only happens at 0900 each day 
            start_q_cardio_consultant = self.env.now
            with self.cardio_consultant.request() as req:
                yield req
                end_q_cardio_consultant = self.env.now
                # need to consider changing this to log normal
                patient.q_time_cardio_consultant = end_q_cardio_consultant - start_q_cardio_consultant
                sampled_cardio_consultant_time = random.expovariate (1.0/ g.mean_cardio_consultant_time)
                yield self.env.timeout(sampled_cardio_consultant_time)

        else: # see a medical consultant 
            
            start_q_medical_consultant = self.env.now
            with self.consultant.request() as req:
                yield req
                end_q_medical_consultant = self.env.now
                # need to consider changing this to log normal
                patient.q_time_medical_consultant = end_q_medical_consultant - start_q_medical_consultant
                sampled_medical_consultant_time = random.expovariate (1.0/ g.mean_medical_consultant_time)
                yield self.env.timeout(sampled_consultant_time)

         # time_in_dept - calculate how long patient in dept in total
        total_time = self.env.now - patient.start_time

        # record outputs
        self.results_df.loc[len(self.results_df)] = {
            "Patient ID": patient.id,
            "Q Time Nurse": patient.q_time_nurse,
            "Time with Nurse": sampled_nurse_time,
            "Q Time Doctor": patient.q_time_doctor,
            "Time with Doctor": sampled_doctor_time,
            "Time for Ix": ix_time,
            "Q Time Consultant": patient.q_time_consultant,
            "Time with Consultant": sampled_consultant_time,
            "Total Journey Time": total_time
        }


# seen by PTWR or cardio PTWR 

# admitted or discharged

# await for medical bed 
