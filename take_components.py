import pandas as pd
import simpy
import random
import streamlit as st 
import os
import uuid
from datetime import datetime

from class_def import g 
from class_def import Patient 
from timing import calculate_hour_of_day
from timing import calculate_day_of_week
from timing import extract_hour
from timing import get_doctor_patient_count
from timing import get_consultant_patient_count
from timing import check_take_doctor_numbers

# generator - patient arrives at hospital
def generator_patient_arrival (self):
    while True:
        self.patient_counter += 1 
        p = Patient (self.patient_counter)
        p.start_time = self.env.now 

        self.env.process (self.attend_hospital (p))

        #randomly sample time to patient arrival
        sampled_inter = random.expovariate (1.0/ g.sdec_patient_inter)
        yield self.env.timeout (sampled_inter)

# function to attend hospital, be given a unique ID and assigned a route 
def attend_hospital (self, patient):
    patient_id = uuid.uuid4()

    attendance_time = self.env.now
    print(f"Patient {patient_id} arrived at time {attendance_time}")
    self.log_event(patient_id, "Arrival to hospital", details=f"Arrival time: {attendance_time}")

    # define patient route here (SDEC, Med Expect, ED)
    poss_patient_route = ["SDEC", "ED", "ED Med Expect"]
    route_probabilities = [g.sdec_probability, g.ed_probability, g.ed_med_expect_probability]

    patient_route = random.choices(poss_patient_route, route_probabilities)[0]

    print(f"Patient {patient_id}'s pathway is {patient_route}")
    self.log_event(patient_id, "Arrival", details=f"Route: {patient_route}")

# nurse triage process 
def nurse_triage():
    start_q_nurse = self.env.now
    # Waiting for nurse
    self.log_event(patient_id, "Start Service", resource="Nurse")
    with self.nurse.request() as req:
        yield req
        end_q_nurse = self.env.now
        # need to consider changing this to log normal
        patient.q_time_nurse = end_q_nurse - start_q_nurse
        sampled_nurse_time = g.min_nurse_time + random.expovariate (1.0/ g.mean_nurse_time)
        yield self.env.timeout(sampled_nurse_time)

    print(f" Patient {patient_id} spent {sampled_nurse_time} with the nurse")

    # Finished with nurse
    self.log_event(patient_id, "Service Complete", resource="Nurse", details=f"Duration: {sampled_nurse_time:.2f}")
                
# function to be clerked by a resident doctor assigned to SDEC only 
def sdec_clerking():
    start_q_doctor = self.env.now
    sdec_used = False
    self.log_event(patient_id, "Request Service", resource="SDEC Doctor")
    with self.sdec_doctor.request() as req_sdec:
        result = yield req_sdec | self.env.timeout(0)  # Try to acquire SDEC doctor immediately
        if req_sdec in result:
            self.log_event(patient_id, "Request Granted", resource="SDEC Doctor", details=f"Immediately")
            sdec_used = True
            end_q_doctor = self.env.now
            patient.q_time_doctor = end_q_doctor - start_q_doctor
            sampled_doctor_time = g.min_doctor_time + random.expovariate(1.0 / g.mean_sdec_doctor_time)
            patient.doctor_type = "SDEC Doctor"
            yield self.env.timeout(sampled_doctor_time)

# function to be seen by a resident doctor who can see patients in A&E and SDEC
def take_clerking():
    with self.take_doctor.request() as req_take:
        self.log_event(patient_id, "Request Granted", resource="Take Doctor", details=f"After failed SDEC Retry")
        yield req_take
        end_q_doctor = self.env.now
        patient.q_time_doctor = end_q_doctor - start_q_doctor
        sampled_doctor_time = g.min_doctor_time + random.expovariate(1.0 / g.mean_take_doctor_time)
        patient.doctor_type = "Take Doctor"
        yield self.env.timeout(sampled_doctor_time)

# function for investigation sink (assumes all happen at once)               
def ix():
    ix_time = g.min_ix_time + random.expovariate(1.0 / g.mean_sdec_ix_time)
    patient.ix_time = ix_time

    print(f"Patient {patient_id} investigations complete")
    self.log_event(patient_id, "Service Complete", resource="Doctor", details=f"Investigations Complete: {ix_time:.2f}")
    yield self.env.timeout(ix_time)

# function for post take ward round by SDEC consultant, leading to admit/ discharge decision 
def sdec_ptwr():
    start_q_consultant = self.env.now
    with self.sdec_consultant.request() as req:
        yield req
        end_q_consultant = self.env.now

        print(f"Patient {patient_id} being seen on PTWR")
        self.log_event(patient_id, "Service Started", resource="PTWR")

        # need to consider changing this to log normal
        patient.q_time_consultant = end_q_consultant - start_q_consultant
        sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_consultant_time)
        
        patient.consultant_type = "SDEC Consultant"
        self.consultant_patient_counter[patient.consultant_type] += 1

        # Decision to admit
        admission_probability = g.prob_sdec_admit 

        if random.random() <= admission_probability:
            # Patient is admitted
            patient.disposition = "admitted"
            self.patient_disposition[patient.disposition] += 1
            #decision_to_admit_time = self.env.now - patient.start_time
        else:
            # Patient is discharged
            patient.disposition = "discharged"
            self.patient_disposition[patient.disposition] += 1

        print(f"The patient {patient_id} was {patient.disposition}")
        self.log_event(patient_id, "Disposition", resource=patient.consultant_type, details=patient.disposition)

        yield self.env.timeout(sampled_consultant_time)

# function for post take ward round by Acute Med consultant, leading to admit/ discharge decision 
def acute_ptwr():
    # request acute consultant
    with self.acute_consultant.request() as req_acute_cons:
        result = yield req_acute_cons | self.env.timeout(0)
        if req_acute_cons in result:
            acute_cons_used = True
            end_q_medical_consultant = self.env.now
            print(f"Patient {patient_id} being seen on medical PTWR")
            # need to consider changing this to log normal
            patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
            sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

            patient.consultant_type = "Acute Consultant"
            self.consultant_patient_counter[patient.consultant_type] += 1

            # Decision to admit
            admission_probability = g.prob_medical_expect_admit 

            if random.random() <= admission_probability:
                # Patient is admitted
                patient.disposition = "admitted"
                self.patient_disposition[patient.disposition] += 1
                #decision_to_admit_time = self.env.now - patient.start_time
            else:
                # Patient is discharged
                patient.disposition = "discharged"
                self.patient_disposition[patient.disposition] += 1
            
            print(f"The patient {patient_id} was {patient.disposition}")

            yield self.env.timeout(sampled_consultant_time)

# function for post take ward round by POD (physician of the day) consultant, leading to admit/ discharge decision 
def pod_ptwr():            
    with self.pod_consultant.request() as req_pod_cons:
        yield req_pod_cons
        end_q_medical_consultant = self.env.now
        print(f"Patient {patient_id} being seen on medical PTWR")
        # need to consider changing this to log normal
        patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
        sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

        patient.consultant_type = "POD Consultant"
        self.consultant_patient_counter[patient.consultant_type] += 1

        # Decision to admit
        admission_probability = g.prob_medical_expect_admit

        if random.random() <= admission_probability:
            # Patient is admitted
            patient.disposition = "admitted"
            self.patient_disposition[patient.disposition] += 1
            #decision_to_admit_time = self.env.now - patient.start_time
        else:
            # Patient is discharged
            patient.disposition = "discharged"
            self.patient_disposition[patient.disposition] += 1

        print(f"The patient {patient_id} was {patient.disposition}")
        self.log_event(patient_id, "Disposition", resource=patient.consultant_type, details=patient.disposition)

# function for post take ward round by Cardio consultant, leading to admit/ discharge decision OR admit overnight
def cardio_ptwr():
    if g.cardio_start <= hour_of_day < g.cardio_finish:
        start_q_cardio_consultant = self.env.now
        with self.cardio_consultant.request() as req:
            yield req
            end_q_cardio_consultant = self.env.now

            print(f"Patient {patient_id} being seen on cardio PTWR")

            # need to consider changing this to log normal
            patient.q_time_consultant = end_q_cardio_consultant - start_q_cardio_consultant
            sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_cardio_consultant_time)

            patient.consultant_type = "Cardio Consultant"
            self.consultant_patient_counter[patient.consultant_type] += 1

            # Decision to admit
            admission_probability = g.prob_cardio_admit 

            if random.random() <= admission_probability:
                # Patient is admitted
                patient.disposition = "admitted"
                self.patient_disposition[patient.disposition] += 1
                #decision_to_admit_time = self.env.now - patient.start_time
            else:
                # Patient is discharged
                patient.disposition = "discharged"
                self.patient_disposition[patient.disposition] += 1

            print(f"The patient {patient_id} was {patient.disposition}")

            yield self.env.timeout(sampled_consultant_time)

    else: 
        patient.disposition = "admitted"
        self.aw_cardio_ptwr_count += 1 

# function to be added to waiting list for an AMU Bed 
def list_for_bed(): 
    self.log_event(patient_id, "Request AMU Bed", resource="AMU Bed", details=f"Add to AMU bed queue")
    start_q_bed = self.env.now
    with self.amu_bed.request() as req:
        yield req
        end_q_bed = self.env.now
        self.log_event(patient_id, "AMU Bed Granted", resource="AMU Bed")

        patient.bed_allocation = end_q_bed

        patient.q_time_bed = end_q_bed - start_q_bed
        print(f"The patient {patient_id} was assigned a bed at {end_q_bed} time")

        #simulate how long the bed is occupied for
        sampled_amu_bed_occupancy_time = g.min_amu_occupancy_time + random.expovariate (1.0/ g.mean_amu_bed_occupancy_time)
        self.log_event(patient_id, "Dsicharged from AMU Bed", resource="AMU Bed", details=f"Time in AMU Bed: {sampled_amu_bed_occupancy_time}")
        yield self.env.timeout(sampled_amu_bed_occupancy_time)

# function to check if SDEC is open (if not patient goes to ED)
def check_sdec_open():
    # check if SDEC is open
    current_time = self.env.now 
    current_day = current_time / 1440

    # first check the day 
    day_of_week = calculate_day_of_week (current_time)
    print(f"The day of the week is {day_of_week}")

    # then check the time 
    hour_of_day = extract_hour (current_time)
    print(f"The time is {hour_of_day}:00")

