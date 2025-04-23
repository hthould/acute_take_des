import pandas as pd
import simpy
import random
import streamlit as st 

from class_def import g, Patient
# from take_components import nurse_triage_process, sdec_clerking_process
# from take_components import med_clerking_process, sdec_ptwr_process, med_ptwr_process


class Model: 

    import take_components

    # constructor
    def __init__(self, run_number):
        
        self.env = simpy.Environment()
        self.patient_counter = 0 # used as a patient ID

        # resources
        self.nurse = simpy.Resource (self.env, 
            capacity = g.number_of_nurses)
        self.doctors = {
            "SDEC Doctor": simpy.Resource(self.env, 
            capacity = g.number_of_sdec_doctors),
            "Take Doctor": simpy.Resource(self.env, 
            capacity = g.number_of_take_doctors),
        }
        self.consultants = {
            "SDEC": simpy.Resource (self.env, 
            capacity = g.number_of_sdec_consultants),
            "Cardio": simpy.Resource(self.env, 
            capacity = g.number_of_acute_med_consultants),
            "Acute": simpy.Resource(env, self.env, 
            capacity = g.number_of_acute_med_consultants),
            "POD": simpy.Resource(self.env, 
            capacity = g.number_of_pod_consultants),
        }
        
        self.amu_bed = simpy.Resource (self.env, 
            capacity = g.number_of_amu_beds)
        self.sdec_cub = simpy.Resource (self.env, g.number_of_sdec_cubicles)
        self.run_number = run_number 


        self.results_df = pd.DataFrame (columns= [
            "Run ID", "Patient ID", "Patient Route", "Q Time Nurse", "Time with Nurse", "Doctor Source",
            "Q Time Doctor", "Time with Doctor", "Time for Ix", "Consultant Source",
            "Q Time Consultant", "Time with Consultant",
            "Disposition Time", "Patient Disposition", "Admission Probability", "Number of patients discharged", 
            "Number of patient admitted", "Q Time AMU Bed", 
            "Number of patients awaiting a bed", "Time to AMU bed", "SDEC Doctor Count",
            "Take Doctor Count", "Cardio Consultant Count", "SDEC Consultant Count", "Acute Consultant Count",
            "POD Consultant Count", "Total Medical Consultant Count" "Total admissions", 
            "Total discharges", "Total seen in SDEC", "Total Med Expect seen in ED", "Total referred by ED", "Total seen in ED"])
        self.results_df.set_index("Patient ID", inplace=True)


        self.mean_q_time_nurse = 0
        self.mean_q_time_doctor = 0
        self.mean_q_time_consultant = 0
        self.mean_q_time_cardio_consultant = 0 
        self.mean_q_time_bed = 0

        self.patient_disposition = {"admitted": 0, "discharged": 0}
        self.patient_route = {"SDEC": 0, "ED Med Expect": 0, "ED": 0}
        self.doctor_patient_counter = {"SDEC Doctor": 0, "Take Doctor": 0}
        self.consultant_patient_counter = {"SDEC Consultant": 0, "Acute Consultant": 0, "POD Consultant": 0, "Cardio Consultant": 0}
       
    # generator - patient arrives at hospital
    def generator_patient_arrival (self):
        while True:
            self.patient_counter += 1 
            p = Patient (self.patient_counter)
            p.start_time = self.env.now 
            self.env.process (self.attend_hospital (p))

            patient_id = self.patient_counter

            print(f"Generating Patient {patient_id} at time {self.env.now}")

            #randomly sample time to patient arrival
            sampled_inter = random.expovariate (1.0/ g.sdec_patient_inter)
            yield self.env.timeout (sampled_inter)

    # patient sent along 1 of 3 pathways - SDEC, med expect in ED, ED referal 
    # pathways involve triage, clerking and review by a consultant, with some 
    # patients being discharged along the way

def attend_hospital (self):

    patient_id = self.patient_counter
    attendance_time = self.env.now

    # define patient route here (SDEC, Med Expect, ED)
    poss_patient_route = ["SDEC", "ED", "ED Med Expect"]
    route_probabilities = [g.sdec_probability, g.ed_probability, g.ed_med_expect_probability]

    patient_route = random.choices(poss_patient_route, route_probabilities)[0]

    print (f"Patient {patient_id}'s pathway is {patient_route}")

    if patient_route == "SDEC":

        # check if SDEC is open
        current_time = self.env.now 
        current_day = current_time / 1440

        # first check the day 
        day_of_week = calculate_day_of_week (current_time)
        print (f"The day of the week is {day_of_week}")

        # then check the time 
        hour_of_day = extract_hour (current_time)
        print (f"The time is {hour_of_day}:00")

        #if day_of_week == g.sdec_day_open:

        if g.sdec_open <= hour_of_day < g.sdec_closed:
            print (f"Patient {patient_id} arrived in SDEC")
            self.patient_route[patient_route] += 1

            yield from self.nurse_triage_process (self.env, self.nurse, Patient, patient_id, g)

            yield from self.sdec_clerking_process (self.env, self.doctors, self.doctor_patient_counter, Patient, patient_id, g)

            yield from self.sdec_ptwr_process (self.env, self.consultants, self.consultant_patient_counter, Patient, patient_id, g)

        else:
            #redirect to ED
            print ("SDEC is closed. Patient transferred to ED")
            patient_route = "ED Med Expect"
            print (f"Patient {patient_id}'s route is now {patient_route}")

            print (f"Medically expected patient (ID {patient_id}) arrived in ED")
            self.patient_route[patient_route] += 1

            yield from self.nurse_triage_process (self.env, self.nurse, Patient, patient_id, g)

            yield from self.med_clerking_process (self.env, self.doctors, self.doctor_patient_counter, Patient, patient_id, g)

            yield from self.med_ptwr_process (self.env, self.consultants, self.consultant_patient_counter, Patient, patient_id, g)
