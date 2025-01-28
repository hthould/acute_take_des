import pandas as pd
import simpy
import random

from class_def import g 
from class_def import Patient 
from timing import calculate_hour_of_day
from timing import calculate_day_of_week
from timing import extract_hour


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
            capacity = g.number_of_acute_med_consultants)
        self.sdec_consultant = simpy.Resource (self.env, 
            capacity = g.number_of_sdec_consultants)
        self.pod_consultant = simpy.Resource (self.env, 
            capacity = g.number_of_pod_consultants)
        self.cardio_consultant = simpy.Resource (self.env, 
            capacity = g.number_of_cardio_consultants)
        self.amu_bed = simpy.Resource (self.env, 
            capacity = g.number_of_amu_beds)
        self.run_number = run_number 
        self.results_df = pd.DataFrame (columns= [
            "Patient ID", "Patient Route", "Q Time Nurse", "Time with Nurse", "Doctor Source",
            "Q Time Doctor", "Time with Doctor", "Time for Ix", "Consultant Source",
            "Q Time Consultant", "Time with Consultant",
            "Disposition Time", "Patient Disposition", "Number of patients discharged", 
            "Number of patient admitted", "Q Time AMU Bed", 
            "Number of patients awaiting a bed", 
            "Total Journey Time"])
        self.results_df.set_index("Patient ID", inplace=True)

        self.mean_q_time_nurse = 0
        self.mean_q_time_doctor = 0
        self.mean_q_time_consultant = 0
        self.mean_q_time_cardio_consultant = 0 
        self.mean_q_time_bed = 0

        #self.sampled_nurse_time = 0

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

    def attend_hospital (self, patient):

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
            hour_of_day = extract_hour (current_time)

            print (f"The time is {hour_of_day}:00")

            if g.sdec_open <= hour_of_day < g.sdec_closed:
            
                print (f"Patient {patient_id} arrived in SDEC")

                # nurse triage process 
                start_q_nurse = self.env.now
                with self.nurse.request() as req:
                    yield req
                    end_q_nurse = self.env.now
                    # need to consider changing this to log normal
                    patient.q_time_nurse = end_q_nurse - start_q_nurse
                    sampled_nurse_time = g.min_nurse_time + random.expovariate (1.0/ g.mean_nurse_time)
                    yield self.env.timeout(sampled_nurse_time)

                print (f" Patient {patient_id} spent {sampled_nurse_time} with the nurse")

                # medical clerking process 
                start_q_doctor = self.env.now
                sdec_used = False
            
                with self.sdec_doctor.request() as req_sdec:
                    result = yield req_sdec | self.env.timeout(0)  # Try to acquire SDEC doctor immediately
                    if req_sdec in result:
                        sdec_used = True
                        end_q_doctor = self.env.now
                        patient.q_time_doctor = end_q_doctor - start_q_doctor
                        sampled_doctor_time = g.min_doctor_time + random.expovariate(1.0 / g.mean_sdec_doctor_time)
                        yield self.env.timeout(sampled_doctor_time)
                    else:
                    # Fallback to using a take doctor if no SDEC doctor is available
                        with self.take_doctor.request() as req_take:
                            yield req_take
                            end_q_doctor = self.env.now
                            patient.q_time_doctor = end_q_doctor - start_q_doctor
                            sampled_doctor_time = g.min_doctor_time + random.expovariate(1.0 / g.mean_take_doctor_time)
                            yield self.env.timeout(sampled_doctor_time)
                
                patient.doctor_type = "SDEC Doctor" if sdec_used else "Take Doctor"

                print (f"Patient {patient_id} seen by {patient.doctor_type}")
            
                # could include a proportion of patients discharged pre-PTWR as a proportion

                # investigation sink
                ix_time = g.min_ix_time + random.expovariate(1.0 / g.mean_sdec_ix_time)
                patient.ix_time = ix_time

                print (f"Patient {patient_id} investigations complete")
                yield self.env.timeout(ix_time)

                # PTWR process 
                start_q_consultant = self.env.now
                with self.sdec_consultant.request() as req:
                    yield req
                    end_q_consultant = self.env.now

                    print (f"Patient {patient_id} being seen on PTWR")

                    # need to consider changing this to log normal
                    patient.q_time_consultant = end_q_consultant - start_q_consultant
                    sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_consultant_time)
                    
                    patient.consultant_type = "SDEC Consultant"

                    # Decision to admit
                    admission_probability = g.prob_sdec_admit 
                    if random.random() < admission_probability:
                        # Patient is admitted
                        patient.disposition = "admitted"
                        #decision_to_admit_time = self.env.now - patient.start_time
                    else:
                        # Patient is discharged
                        patient.disposition = "discharged"

                    yield self.env.timeout(sampled_consultant_time)

            else:
                #redirect to ED
                print ("SDEC is closed. Patient transferred to ED")
                patient_route = "ED Med Expect"
                print (f"Patient {patient_id}'s route is now {patient_route}")
                print (f"Medically expected patient (ID {patient_id}) arrived in ED")

                # nurse triage process 
                start_q_nurse = self.env.now
                with self.nurse.request() as req:
                    yield req
                    end_q_nurse = self.env.now
                    # need to consider changing this to log normal
                    patient.q_time_nurse = end_q_nurse - start_q_nurse
                    sampled_nurse_time = g.min_nurse_time + random.expovariate (1.0/ g.mean_nurse_time)
                    yield self.env.timeout(sampled_nurse_time)
                
                print (f" Patient {patient_id} spent {sampled_nurse_time} with the nurse")

                # doctor clerking process 
                start_q_take_doctor = self.env.now
                with self.take_doctor.request() as req:
                    yield req
                    end_q_take_doctor = self.env.now
                    # need to consider changing this to log normal
                    patient.q_time_take_doctor = end_q_take_doctor - start_q_take_doctor
                    sampled_doctor_time = g.min_doctor_time + random.expovariate (1.0/ g.mean_take_doctor_time)
                    yield self.env.timeout(sampled_doctor_time)

                    # Need to add in discharge probability here 

                patient.doctor_type = "Take Doctor"
                print (f"Patient {patient_id} seen by {patient.doctor_type}")

                # Assign PTWR status here - cardio vs medical
                patient.flow = "cardio" if random.random() < g.prob_needs_cardioptwr else "medical"

                # investigation sink
                ix_time = g.min_ix_time + random.expovariate(1.0 / g.mean_ed_med_expect_ix_time)
                patient.ix_time = ix_time
                yield self.env.timeout(ix_time)

                print (f"Investigations complete for patient {patient_id}")

                # PTWR process: can either see a cardiology consultant or a medical consultant
                # dependent on probability (proportion cardio v medicine)

                if  patient.flow == "cardio":

                    #patient.disposition = "admitted"

                    # cardio PTWR only happens at 0900 each day, essentially admitted 
                    start_q_cardio_consultant = self.env.now
                    with self.cardio_consultant.request() as req:
                        yield req
                        end_q_cardio_consultant = self.env.now

                        print (f"Patient {patient_id} being seen on cardio PTWR")

                        # need to consider changing this to log normal
                        patient.q_time_consultant = end_q_cardio_consultant - start_q_cardio_consultant
                        sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_cardio_consultant_time)

                        patient.consultant_type = "Cardio Consultant"
                        
                
                    '''else:
                        patient.disposition = "admitted"
                        # Wait until the start of the next working hour
                        next_working_hour = max(g.cardio_start, hour_of_day + 1)
                        wait_time = (next_working_hour - hour_of_day) * 60  # Convert hours to minutes
                        yield self.env.timeout(wait_time)'''

                    # Decision to admit
                    admission_probability = g.prob_cardio_admit 
                    if random.random() < admission_probability:
                        # Patient is admitted
                        patient.disposition = "admitted"
                        #decision_to_admit_time = self.env.now - patient.start_time
                    else:
                        # Patient is discharged
                        patient.disposition = "discharged"

                    yield self.env.timeout(sampled_consultant_time)

                else: # see a medical consultant 
                    
                    start_q_medical_consultant = self.env.now
                    acute_cons_used = False

                    # request acute consultant
                    with self.acute_consultant.request() as req_acute_cons:
                        result = yield req_acute_cons | self.env.timeout(0)
                        if req_acute_cons in result:
                            acute_cons_used = True
                            end_q_medical_consultant = self.env.now
                            print (f"Patient {patient_id} being seen on medical PTWR")
                            # need to consider changing this to log normal
                            patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
                            sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

                            patient.consultant_type = "Acute Consultant"

                            # Decision to admit
                            admission_probability = g.prob_medical_expect_admit 
                            if random.random() < admission_probability:
                                # Patient is admitted
                                patient.disposition = "admitted"
                                #decision_to_admit_time = self.env.now - patient.start_time
                            else:
                                # Patient is discharged
                                patient.disposition = "discharged"

                            yield self.env.timeout(sampled_consultant_time)
                
                        # otherwise use the POD
                        else:
                            with self.pod_consultant.request() as req_pod_cons:
                                yield req_pod_cons
                                end_q_medical_consultant = self.env.now
                                print (f"Patient {patient_id} being seen on medical PTWR")
                                # need to consider changing this to log normal
                                patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
                                sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

                                patient.consultant_type = "POD Consultant"

                                # Decision to admit
                                admission_probability = g.prob_medical_expect_admit 
                                if random.random() < admission_probability:
                                    # Patient is admitted
                                    patient.disposition = "admitted"
                                    #decision_to_admit_time = self.env.now - patient.start_time
                                else:
                                    # Patient is discharged
                                    patient.disposition = "discharged"

                    patient.PTWR_type = "Acute Consultant" if acute_cons_used else "POD Consultant"

        elif patient_route == "ED Med Expect":
        
            print (f"Medically expected patient (ID {patient_id}) arrived in ED")

            # nurse triage process 
            start_q_nurse = self.env.now
            with self.nurse.request() as req:
                yield req
                end_q_nurse = self.env.now
                # need to consider changing this to log normal
                patient.q_time_nurse = end_q_nurse - start_q_nurse
                sampled_nurse_time = g.min_nurse_time + random.expovariate (1.0/ g.mean_nurse_time)
                yield self.env.timeout(sampled_nurse_time)

            print (f" Patient {patient_id} spent {sampled_nurse_time} with the nurse")

            # doctor clerking process 
            start_q_take_doctor = self.env.now
            with self.take_doctor.request() as req:
                yield req
                end_q_take_doctor = self.env.now
                # need to consider changing this to log normal
                patient.q_time_take_doctor = end_q_take_doctor - start_q_take_doctor
                sampled_doctor_time = g.min_doctor_time + random.expovariate (1.0/ g.mean_take_doctor_time)
                yield self.env.timeout(sampled_doctor_time)

                # Need to add in discharge probability here 

            patient.doctor_type = "Take Doctor"
            print (f"Patient {patient_id} seen by {patient.doctor_type}")

            # Assign PTWR status here - cardio vs medical
            patient.flow = "cardio" if random.random() < g.prob_needs_cardioptwr else "medical"

            # investigation sink
            ix_time = g.min_ix_time + random.expovariate(1.0 / g.mean_ed_med_expect_ix_time)
            patient.ix_time = ix_time
            yield self.env.timeout(ix_time)

            print (f"Investigations complete for patient {patient_id}")

            # PTWR process: can either see a cardiology consultant or a medical consultant
            # dependent on probability (proportion cardio v medicine)

            if  patient.flow == "cardio":

                patient.disposition = "admitted"

                # cardio PTWR only happens at 0900 each day, essentially admitted 
                start_q_cardio_consultant = self.env.now
                with self.cardio_consultant.request() as req:
                    yield req
                    end_q_cardio_consultant = self.env.now

                    print (f"Patient {patient_id} being seen on cardio PTWR")

                    # need to consider changing this to log normal
                    patient.q_time_consultant = end_q_cardio_consultant - start_q_cardio_consultant
                    sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_cardio_consultant_time)

                    patient.consultant_type = "Cardio Consultant"

                    # Decision to admit
                    admission_probability = g.prob_cardio_admit 
                    if random.random() < admission_probability:
                        # Patient is admitted
                        patient.disposition = "admitted"
                        #decision_to_admit_time = self.env.now - patient.start_time
                    else:
                        # Patient is discharged
                        patient.disposition = "discharged"

                    yield self.env.timeout(sampled_consultant_time)

            else: # see a medical consultant 
                
                start_q_medical_consultant = self.env.now
                acute_cons_used = False

                # request acute consultant
                with self.acute_consultant.request() as req_acute_cons:
                    result = yield req_acute_cons | self.env.timeout(0)
                    if req_acute_cons in result:
                        acute_cons_used = True
                        end_q_medical_consultant = self.env.now
                        print (f"Patient {patient_id} being seen on medical PTWR")
                        # need to consider changing this to log normal
                        patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
                        sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

                        patient.consultant_type = "Acute Consultant"

                        # Decision to admit
                        admission_probability = g.prob_medical_expect_admit 
                        if random.random() < admission_probability:
                            # Patient is admitted
                            patient.disposition = "admitted"
                            #decision_to_admit_time = self.env.now - patient.start_time
                        else:
                            # Patient is discharged
                            patient.disposition = "discharged"

                        yield self.env.timeout(sampled_consultant_time)
            
                    # otherwise use the POD
                    else:
                        with self.pod_consultant.request() as req_pod_cons:
                            yield req_pod_cons
                            end_q_medical_consultant = self.env.now
                            print (f"Patient {patient_id} being seen on medical PTWR")
                            # need to consider changing this to log normal
                            patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
                            sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

                            patient.consultant_type = "POD Consultant"

                            # Decision to admit
                            admission_probability = g.prob_medical_expect_admit 
                            if random.random() < admission_probability:
                                # Patient is admitted
                                patient.disposition = "admitted"
                                #decision_to_admit_time = self.env.now - patient.start_time
                            else:
                                # Patient is discharged
                                patient.disposition = "discharged"

                patient.PTWR_type = "Acute Consultant" if acute_cons_used else "POD Consultant"

        else:
        
            print (f"Patient {patient_id} referred from ED")

            # patient has already been triaged and seen a nurse so doesn't need to see them again
            sampled_nurse_time = 0

            # doctor clerking process 
            start_q_take_doctor = self.env.now
            with self.take_doctor.request() as req:
                yield req
                end_q_take_doctor = self.env.now
                # need to consider changing this to log normal
                patient.q_time_take_doctor = end_q_take_doctor - start_q_take_doctor
                sampled_doctor_time = g.min_doctor_time + random.expovariate (1.0/ g.mean_take_doctor_time)
                yield self.env.timeout(sampled_doctor_time)

                # Need to add in discharge probability here 
            
            patient.doctor_type = "Take Doctor"
            print (f"Patient {patient_id} seen by {patient.doctor_type}")

            # Assign PTWR status here - cardio vs medical
            patient.flow = "cardio" if random.random() < g.prob_needs_cardioptwr else "medical"


            # investigation sink
            ix_time = g.min_ed_ix_time + random.expovariate(1.0 / g.mean_ed_ix_time)
            patient.ix_time = ix_time
            yield self.env.timeout(ix_time)

            print (f"Investigations complete for patient {patient_id}")

            # PTWR process: can either see a cardiology consultant or a medical consultant
            # dependent on probability (proportion cardio v medicine)

            if  patient.flow == "cardio":

                patient.disposition = "admitted"

                # cardio PTWR only happens at 0900 each day, essentially admitted 
                start_q_cardio_consultant = self.env.now
                with self.cardio_consultant.request() as req:
                    yield req
                    end_q_cardio_consultant = self.env.now
                    print (f"Patient {patient_id} being seen on cardio PTWR")
                    # need to consider changing this to log normal
                    patient.q_time_consultant = end_q_cardio_consultant - start_q_cardio_consultant
                    sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_cardio_consultant_time)

                    patient.consultant_type = "Cardio Consultant"

                    # Decision to admit
                    admission_probability = g.prob_cardio_admit 
                    if random.random() < admission_probability:
                        # Patient is admitted
                        patient.disposition = "admitted"
                        #decision_to_admit_time = self.env.now - patient.start_time
                    else:
                        # Patient is discharged
                        patient.disposition = "discharged"

                    yield self.env.timeout(sampled_consultant_time)

            else: # see a medical consultant 
            
                start_q_medical_consultant = self.env.now
                acute_cons_used = False

                # request acute consultant
                with self.acute_consultant.request() as req_acute_cons:
                    result = yield req_acute_cons | self.env.timeout(0)
                    if req_acute_cons in result:
                        acute_cons_used = True
                        end_q_medical_consultant = self.env.now
                        print (f"Patient {patient_id} being seen on medical PTWR")
                        # need to consider changing this to log normal
                        patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
                        sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

                        patient.consultant_type = "Acute Consultant"

                        # Decision to admit
                        admission_probability = g.prob_medical_expect_admit 
                        if random.random() < admission_probability:
                            # Patient is admitted
                            patient.disposition = "admitted"
                            #decision_to_admit_time = self.env.now - patient.start_time
                        else:
                            # Patient is discharged
                            patient.disposition = "discharged"

                        yield self.env.timeout(sampled_consultant_time)
            
                    # otherwise use the POD
                    else:
                        with self.pod_consultant.request() as req_pod_cons:
                            yield req_pod_cons
                            end_q_medical_consultant = self.env.now
                            print (f"Patient {patient_id} being seen on medical PTWR")
                            # need to consider changing this to log normal
                            patient.q_time_consultant = end_q_medical_consultant - start_q_medical_consultant
                            sampled_consultant_time = g.min_consultant_time + random.expovariate (1.0/ g.mean_medical_consultant_time)

                            patient.consultant_type = "POD Consultant"

                            # Decision to admit
                            admission_probability = g.prob_medical_expect_admit 
                            if random.random() < admission_probability:
                                # Patient is admitted
                                patient.disposition = "admitted"
                                
                            else:
                                # Patient is discharged
                                patient.disposition = "discharged"

                patient.PTWR_type = "Acute Consultant" if acute_cons_used else "POD Consultant"
        
        print (f"Patient {patient_id}'s disposition is {patient.disposition}")

        # timestamp for admission decision 
        decision_to_admit_time = self.env.now - patient.start_time

        # queue for a bed
        if patient.disposition == "admitted":
            start_q_bed = self.env.now
            with self.amu_bed.request() as req:
                yield req
                end_q_bed = self.env.now

                patient.q_time_bed = end_q_bed - start_q_bed
                print (f"The patient {patient_id} was assigned a bed at {end_q_bed} time")

                # simulate how long the bed is occupied for
                sampled_amu_bed_occupancy_time = g.min_amu_occupancy_time + random.expovariate (1.0/ g.mean_amu_bed_occupancy_time)
                yield self.env.timeout(sampled_amu_bed_occupancy_time)

        elif patient.disposition == "discharged":
            print (f"Patient {patient_id} was discharged")

        # time_in_dept - calculate how long patient in dept until getting a bed
        total_time = self.env.now - patient.time_patient_got_bed

        # record outputs
        if attendance_time > g.warm_up_period:
            self.results_df.loc[len(self.results_df)] = {
                "Patient ID": patient.id,
                "Patient Route": patient_route,
                "Q Time Nurse": patient.q_time_nurse, 
                #"Time with Nurse": sampled_nurse_time,
                "Time with Nurse": getattr(patient, "sampled_nurse_time", 0.0),
                "Doctor Source": patient.doctor_type,
                "Q Time Doctor": patient.q_time_doctor,
                "Time with Doctor": sampled_doctor_time,
                "Time for Ix": ix_time,
                "Consultant Source": patient.consultant_type,
                "Q Time Consultant": patient.q_time_consultant,
                "Time with Consultant": sampled_consultant_time,
                "Disposition Time": decision_to_admit_time,
                "Patient Disposition": patient.disposition,
                "Q Time AMU Bed": patient.q_time_bed,
                "Total Journey Time": total_time,
                }

    def calculate_run_result (self):
        self.mean_q_time_nurse = self.results_df["Q Time Nurse"].mean()
        self.mean_q_time_take_doctor = self.results_df["Q Time Doctor"].mean()
        self.mean_q_time_consultant = self.results_df["Q Time Consultant"].mean()
        self.mean_queue_time_bed = self.results_df ["Q Time AMU Bed"].mean()
        self.mean_journey_time = self.results_df["Total Journey Time"].mean()

        #"Number of patients discharged": 
        #"Number of patient admitted", 
        #"Number of patients awaiting a bed"

    def run (self):
        self.env.process(self.generator_patient_arrival())
        self.env.run(until = g.sim_duration)
        self.calculate_run_result()

        print (f"Run Number {self.run_number}")
        print (self.results_df)


#Trial class
class Trial:

    # dataframe for trial results 
    def  __init__(self):
        self.df_trial_results = pd.DataFrame(columns=[
            "Run Number","Average Patients per Run", "Average No Patients clerked",
            "Mean Q Time Nurse", "Mean Q Time Take Doctor","Average No Patients seen by Cardio", 
            "Average No Patients seen by Medicine",
            "Mean Q Time Consultant", "Number of patients discharged", 
            "Number of patient admitted", "Q Time AMU Bed", 
            "Number of patients awaiting a bed", "Mean Journey Time"
        ])

    # print and record trial results
    def print_trial_results(self):
        print ("Trial Results")
        print (self.df_trial_results)
        # need to save to a PDF or table here 

    #run the trial!
    def run_trial(self):
        for run in range(g.number_of_runs):
            medical_take_model = Model(run)
            medical_take_model.run ()

            self.df_trial_results.loc[len(self.df_trial_results)] = {
                "Run Number": run,
                "Mean Q Time Nurse": medical_take_model.mean_q_time_nurse,
                #"Average Patients per Run":
                #"Average No Patients Clerked":
                "Mean Q Time Take Doctor": medical_take_model.mean_q_time_take_doctor,
                #"Average No Patients seen by Cardio":
                #"Average No Patients seen by Medicine":
                "Mean Q Time Consultant": medical_take_model.mean_q_time_consultant,
                #"Number of patients discharged", 
                #"Number of patient admitted", 
                "Q Time AMU Bed": medical_take_model.mean_q_time_bed,
                #"Number of patients awaiting a bed"
                "Mean Journey Time": medical_take_model.mean_journey_time
            }
        self.print_trial_results()

print ("Model warming up")

trial_1 = Trial ()
trial_1.run_trial()
