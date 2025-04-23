import pandas as pd
import simpy
import random

# from class_def import g, Patient
from timing import calculate_hour_of_day
from timing import calculate_day_of_week
from timing import extract_hour
from timing import get_doctor_patient_count
from timing import get_consultant_patient_count
from timing import check_take_doctor_numbers

def check_sdec_open (self, patient, patient_id, g):
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

    else:
        #redirect to ED
        print ("SDEC is closed. Patient transferred to ED")
        patient_route = "ED Med Expect"
        print (f"Patient {patient_id}'s route is now {patient_route}")

        print (f"Medically expected patient (ID {patient_id}) arrived in ED")
        self.patient_route[patient_route] += 1

def nurse_triage_process (self, env, nurse, patient, patient_id, g):
    start_q_nurse = self.env.now
    with self.nurse.request() as req:
        yield req
        end_q_nurse = self.env.now
        # need to consider changing this to log normal
        patient.q_time_nurse = end_q_nurse - start_q_nurse
        sampled_nurse_time = g.min_nurse_time + random.expovariate (1.0/ g.mean_nurse_time)
        yield self.env.timeout(sampled_nurse_time)
    
    print (f" Patient {patient_id} spent {sampled_nurse_time} with the nurse")
    return (sampled_nurse_time)

def sdec_clerking_process (self, env, doctors, doctor_patient_counter, patient, patient_id, g): 
    start_q_doctor = self.env.now
    sdec_used = False

    with self.doctors["SDEC Doctor"].request() as req:
        result = yield req_sdec | self.env.timeout(0)  # Try to acquire SDEC doctor immediately
        if req_sdec in result:
            sdec_used = True
            end_q_doctor = self.env.now
            patient.q_time_doctor = end_q_doctor - start_q_doctor
            sampled_doctor_time = g.min_doctor_time + random.expovariate(1.0 / g.mean_sdec_doctor_time)
            yield self.env.timeout(sampled_doctor_time)
    
        else:
        # Fallback to using a take doctor if no SDEC doctor is available
            with self.doctors["Take Doctor"].request() as req_take:
                yield req_take
                end_q_doctor = self.env.now
                patient.q_time_doctor = end_q_doctor - start_q_doctor
                sampled_doctor_time = g.min_doctor_time + random.expovariate(1.0 / g.mean_take_doctor_time)
                yield self.env.timeout(sampled_doctor_time)
    
    patient.doctor_type = "SDEC Doctor" if sdec_used else "Take Doctor"
    self.doctor_patient_counter[patient.doctor_type] += 1

    print (f"Patient {patient_id} seen by {patient.doctor_type}")

    # could include a proportion of patients discharged pre-PTWR as a proportion

    # investigation sink
    ix_time = g.min_ix_time + random.expovariate(1.0 / g.mean_sdec_ix_time)
    patient.ix_time = ix_time

    print (f"Patient {patient_id} investigations complete")
    yield self.env.timeout(ix_time)

    return (sampled_doctor_time, ix_time)

def med_clerking_process (self, env, doctors, doctor_patient_counter, patient, patient_id, g):
    start_q_take_doctor = self.env.now
    with self.doctors ["Take Doctor"].request() as req:
        yield req
        end_q_take_doctor = self.env.now
        # need to consider changing this to log normal
        patient.q_time_take_doctor = end_q_take_doctor - start_q_take_doctor
        sampled_doctor_time = g.min_doctor_time + random.expovariate (1.0/ g.mean_take_doctor_time)
        yield self.env.timeout(sampled_doctor_time)

        # Need to add in discharge probability here 

    patient.doctor_type = "Take Doctor"
    self.doctor_patient_counter[patient.doctor_type] += 1
    print (f"Patient {patient_id} seen by {patient.doctor_type}")

    # Assign PTWR status here - cardio vs medical
    patient.flow = "cardio" if random.random() < g.prob_needs_cardioptwr else "medical"
    
    # investigation sink
    ix_time = g.min_ix_time + random.expovariate(1.0 / g.mean_ed_med_expect_ix_time)
    patient.ix_time = ix_time
    yield self.env.timeout(ix_time)

    print (f"Investigations complete for patient {patient_id}")

    yield from self.med_ptwr_process (patient, patient_id, g)

    return (sampled_doctor_time, ix_time)

def sdec_ptwr_process (self, env, consultants, consultant_patient_counter, patient, patient_id, g, patient_disposition):
    start_q_consultant = self.env.now
    with self.consultants["SDEC"].request() as req:
        yield req
        end_q_consultant = self.env.now

        print (f"Patient {patient_id} being seen on PTWR")

        # need to consider changing this to log normal
        patient.q_time_consultant = end_q_consultant - start_q_consultant
        sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_consultant_time)
        
        patient.consultant_type = "SDEC Consultant"
        self.consultant_patient_counter[patient.consultant_type] += 1

    # Decision to admit
    admission_probability = g.prob_sdec_admit 
    print (f"The admission probability for patient {patient_id} was {admission_probability}")

    if random.random() <= admission_probability:
        # Patient is admitted
        patient.disposition = "admitted"
        self.patient_disposition[patient.disposition] += 1
        #decision_to_admit_time = self.env.now - patient.start_time
    else:
        # Patient is discharged
        patient.disposition = "discharged"
        self.patient_disposition[patient.disposition] += 1

    print (f"The patient {patient_id} was {patient.disposition}")

    yield self.env.timeout(sampled_consultant_time)
    return (sampled_consultant_time)

def med_ptwr_process(self, env, consultants, consultant_patient_counter, patient, patient_id, g, patient_disposition): 
    if  patient.flow == "cardio":

        #patient.disposition = "admitted"

        # cardio PTWR only happens at 0900 each day, essentially admitted 
        start_q_cardio_consultant = self.env.now
        with self.consultants["Cardio"].request() as req:
            yield req
            end_q_cardio_consultant = self.env.now

            print (f"Patient {patient_id} being seen on cardio PTWR")

            # need to consider changing this to log normal
            patient.q_time_consultant = end_q_cardio_consultant - start_q_cardio_consultant
            sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_cardio_consultant_time)

            patient.consultant_type = "Cardio Consultant"
            self.consultant_patient_counter[patient.consultant_type] += 1

            # Decision to admit
            admission_probability = g.prob_cardio_admit 
            print (f"The admission probability for patient {patient_id} was {admission_probability}")
            if random.random() <= admission_probability:
                # Patient is admitted
                patient.disposition = "admitted"
                self.patient_disposition[patient.disposition] += 1
                #decision_to_admit_time = self.env.now - patient.start_time
            else:
                # Patient is discharged
                patient.disposition = "discharged"
                self.patient_disposition[patient.disposition] += 1
                
            print (f"The patient {patient_id} was {patient.disposition}")

            yield self.env.timeout(sampled_consultant_time)

    else: # see a medical consultant 
        
        start_q_medical_consultant = self.env.now
        acute_cons_used = False

        # request acute consultant
        with self.consultants["Acute"].request() as req_acute_cons:
            result = yield req_acute_cons | self.env.timeout(0)
            if req_acute_cons in result:
                acute_cons_used = True
                end_q_medical_consultant = self.env.now
                print (f"Patient {patient_id} being seen on medical PTWR")
                # need to consider changing this to log normal
                patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
                sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

                patient.consultant_type = "Acute Consultant"
                self.consultant_patient_counter[patient.consultant_type] += 1

                # Decision to admit
                admission_probability = g.prob_medical_expect_admit 
                print (f"The admission probability for patient {patient_id} was {admission_probability}")
                if random.random() <= admission_probability:
                    # Patient is admitted
                    patient.disposition = "admitted"
                    self.patient_disposition[patient.disposition] += 1
                    #decision_to_admit_time = self.env.now - patient.start_time
                else:
                    # Patient is discharged
                    patient.disposition = "discharged"
                    self.patient_disposition[patient.disposition] += 1
                
                print (f"The patient {patient_id} was {patient.disposition}")

                yield self.env.timeout(sampled_consultant_time)

            # otherwise use the POD
            else:
                with self.consultants["POD"].request() as req_pod_cons:
                    yield req_pod_cons
                    end_q_medical_consultant = self.env.now
                    print (f"Patient {patient_id} being seen on medical PTWR")
                    # need to consider changing this to log normal
                    patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
                    sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

                    patient.consultant_type = "POD Consultant"
                    self.consultant_patient_counter[patient.consultant_type] += 1

                    # Decision to admit
                    admission_probability = g.prob_medical_expect_admit
                    print (f"The admission probability for patient {patient_id} was {admission_probability}")
                    if random.random() <= admission_probability:
                        # Patient is admitted
                        patient.disposition = "admitted"
                        self.patient_disposition[patient.disposition] += 1
                        #decision_to_admit_time = self.env.now - patient.start_time
                    else:
                        # Patient is discharged
                        patient.disposition = "discharged"
                        self.patient_disposition[patient.disposition] += 1

                    print (f"The patient {patient_id} was {patient.disposition}")

        patient.PTWR_type = "Acute Consultant" if acute_cons_used else "POD Consultant"

def wait_for_amu_bed (self, patient, patient.disposition): 

    # queue for a bed
    if patient.disposition == "admitted":
        start_q_bed = self.env.now
        with self.amu_bed.request() as req:
            yield req
            end_q_bed = self.env.now

            patient.bed_allocation = end_q_bed

            #print (f"The patient {patient_id} was allocated a bed at {patient.bed_allocation}")

            patient.q_time_bed = end_q_bed - start_q_bed
            print (f"The patient {patient_id} was assigned a bed at {end_q_bed} time")

            # simulate how long the bed is occupied for
            #sampled_amu_bed_occupancy_time = g.min_amu_occupancy_time + random.expovariate (1.0/ g.mean_amu_bed_occupancy_time)
            #yield self.env.timeout(sampled_amu_bed_occupancy_time)

    elif patient.disposition == "discharged":
        print (f"Patient {patient_id} was discharged")