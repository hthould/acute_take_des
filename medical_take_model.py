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

    # define patient route here (SDEC, Med Expect, ED)
    patient_route = "SDEC" or "ED" or "ED Med Expect"

    if patient_route == "SDEC":
        
        print ("Patient arrived in SDEC")

        # nurse triage process 
        start_q_nurse = self.env.now
        with self.nurse.request() as req:
            yield req
            end_q_nurse = self.env.now
            # need to consider changing this to log normal
            patient.q_time_nurse = end_q_nurse - start_q_nurse
            sampled_nurse_time = random.expovariate (1.0/ g.mean_nurse_time)
            yield self.env.timeout(sampled_nurse_time)

        # medical clerking process 
        start_q_doctor = self.env.now
        sdec_used = False
        
        with self.sdec_doctor.request() as req_sdec:
            result = yield req_sdec | self.env.timeout(0)  # Try to acquire SDEC doctor immediately
            if req_sdec in result:
                sdec_used = True
                end_q_doctor = self.env.now
                patient.q_time_doctor = end_q_doctor - start_q_doctor
                sampled_doctor_time = random.expovariate(1.0 / g.mean_sdec_doctor_time)
                yield self.env.timeout(sampled_doctor_time)
            else:
            # Fallback to using a take doctor if no SDEC doctor is available
                with self.take_doctor.request() as req_take:
                    yield req_take
                    end_q_doctor = self.env.now
                    patient.q_time_doctor = end_q_doctor - start_q_doctor
                    sampled_doctor_time = random.expovariate(1.0 / g.mean_take_doctor_time)
                    yield self.env.timeout(sampled_doctor_time)
           
        patient.doctor_type = "SDEC Doctor" if sdec_used else "Take Doctor"
        
        # could include a proportion of patients discharged pre-PTWR as a proportion

        # investigation sink
        ix_time = random.expovariate(1.0 / g.mean_sdec_ix_time)
        patient.ix_time = ix_time
        yield self.env.timeout(ix_time)

        # PTWR process 
        start_q_consultant = self.env.now
        with self.consultant.request() as req:
            yield req
            end_q_consultant = self.env.now
            # need to consider changing this to log normal
            patient.q_time_consultant = end_q_consultant - start_q_consultant
            sampled_consultant_time = random.expovariate (1.0/ g.mean_consultant_time)
            
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

        # timestamp for admission decision 
        decision_to_admit_time = self.env.now - patient.start_time

         # time_in_dept - calculate how long patient in dept in total
        total_time = self.env.now - patient.start_time

        # record outputs
        self.results_df.loc[len(self.results_df)] = {
            "Patient ID": patient.id,
            "Patient Route": patient_route,
            "Q Time Nurse": patient.q_time_nurse,
            "Time with Nurse": sampled_nurse_time,
            "Q Time Doctor": patient.q_time_doctor,
            "Time with Doctor": sampled_doctor_time,
            "Doctor Source": patient.doctor_type,
            "Time for Ix": ix_time,
            "Q Time Consultant": patient.q_time_consultant,
            "Time with Consultant": sampled_consultant_time,
            "Disposition Time": decision_to_admit_time,
            "Patient Disposition": patient.disposition,
            "Total Journey Time": total_time
        }


    elif patient_route == "ED Med Expect":
    
         print ("Patient arrived in ED")

         # nurse triage process 
        start_q_nurse = self.env.now
        with self.nurse.request() as req:
            yield req
            end_q_nurse = self.env.now
            # need to consider changing this to log normal
            patient.q_time_nurse = end_q_nurse - start_q_nurse
            sampled_nurse_time = random.expovariate (1.0/ g.mean_nurse_time)
            yield self.env.timeout(sampled_nurse_time)

        # doctor clerking process 
        start_q_take_doctor = self.env.now
        with self.take_doctor.request() as req:
            yield req
            end_q_take_doctor = self.env.now
            # need to consider changing this to log normal
            patient.q_time_take_doctor = end_q_take_doctor - start_q_take_doctor
            sampled_take_doctor_time = random.expovariate (1.0/ g.mean_take_doctor_time)
            yield self.env.timeout(sampled_take_doctor_time)

            # Need to add in discharge probability here 
        
        #print ("Patient has been clerked")

        # Assign PTWR status here - cardio vs medical
        patient.flow = "cardio" if random.random() < g.prob_needs_cardioptwr else "medical"

        # investigation sink
        ix_time = random.expovariate(1.0 / g.mean_ed_med_expect_ix_time)
        patient.ix_time = ix_time
        yield self.env.timeout(ix_time)

        #print ("Investigations complete")

        # PTWR process: can either see a cardiology consultant or a medical consultant
        # dependent on probability (proportion cardio v medicine)

        if  patient.flow == "cardio":

            patient.disposition = "admitted"

            # cardio PTWR only happens at 0900 each day, essentially admitted 
            start_q_cardio_consultant = self.env.now
            with self.cardio_consultant.request() as req:
                yield req
                end_q_cardio_consultant = self.env.now
                #print ("Patient being seen on cardio PTWR")
                # need to consider changing this to log normal
                patient.q_time_cardio_consultant = end_q_cardio_consultant - start_q_cardio_consultant
                sampled_cardio_consultant_time = random.expovariate (1.0/ g.mean_cardio_consultant_time)

                # Decision to admit
                admission_probability = g.prob_cardio_admit 
                if random.random() < admission_probability:
                    # Patient is admitted
                    patient.disposition = "admitted"
                    #decision_to_admit_time = self.env.now - patient.start_time
                else:
                    # Patient is discharged
                    patient.disposition = "discharged"

                yield self.env.timeout(sampled_cardio_consultant_time)

        else: # see a medical consultant 
            
            start_q_medical_consultant = self.env.now
            with self.medical_consultant.request() as req:
                yield req
                end_q_medical_consultant = self.env.now
                #print ("Patient being seen on medical PTWR")
                # need to consider changing this to log normal
                patient.q_time_medical_consultant = end_q_medical_consultant - start_q_medical_consultant
                sampled_medical_consultant_time = random.expovariate (1.0/ g.mean_medical_consultant_time)

                # Decision to admit
                admission_probability = g.prob_medical_expect_admit 
                if random.random() < admission_probability:
                    # Patient is admitted
                    patient.disposition = "admitted"
                    #decision_to_admit_time = self.env.now - patient.start_time
                else:
                    # Patient is discharged
                    patient.disposition = "discharged"

                yield self.env.timeout(sampled_medical_consultant_time)
        
        # timestamp for admission decision 
        decision_to_admit_time = self.env.now - patient.start_time

        # time_in_dept - calculate how long patient in dept in total
        total_time_ed = self.env.now - patient.start_time

        # record outputs
        self.results_df.loc[len(self.results_df)] = {
            "Patient ID": patient.id,
            "Patient Route": patient_route,
            "Q Time Nurse": patient.q_time_nurse,
            "Time with Nurse": sampled_nurse_time,
            "Q Time Take Doctor": patient.q_time_take_doctor,
            "Time with Take Doctor": sampled_take_doctor_time,
            "Time for Ix": ix_time,
            "Type of PTWR": patient.flow,
            "Q Time Cardio Consultant": getattr(patient, "q_time_cardio_consultant", 0.0),
            "Q Time Medical Consultant": getattr(patient, "q_time_medical_consultant", 0.0),
            "Time with Cardio Consultant": sampled_cardio_consultant_time if patient.flow == "cardio" else 0.0,
            "Time with Medical Consultant": sampled_medical_consultant_time if patient.flow == "medical" else 0.0,
            "Disposition Time": decision_to_admit_time,
            "Patient Disposition": patient.disposition,
            "Total Journey Time": total_time_ed
        }

    else:
    
        print ("Patient referred from ED")

        # doctor clerking process 
        start_q_take_doctor = self.env.now
        with self.take_doctor.request() as req:
            yield req
            end_q_take_doctor = self.env.now
            # need to consider changing this to log normal
            patient.q_time_take_doctor = end_q_take_doctor - start_q_take_doctor
            sampled_take_doctor_time = random.expovariate (1.0/ g.mean_take_doctor_time)
            yield self.env.timeout(sampled_take_doctor_time)

            # Need to add in discharge probability here 
        
        #print ("Patient has been clerked")

        # Assign PTWR status here - cardio vs medical
        patient.flow = "cardio" if random.random() < g.prob_needs_cardioptwr else "medical"


        # investigation sink
        ix_time = random.expovariate(1.0 / g.mean_ed_ix_time)
        patient.ix_time = ix_time
        yield self.env.timeout(ix_time)

        #print ("Investigations complete")

        # PTWR process: can either see a cardiology consultant or a medical consultant
        # dependent on probability (proportion cardio v medicine)

        if  patient.flow == "cardio":

            patient.disposition = "admitted"

            # cardio PTWR only happens at 0900 each day, essentially admitted 
            start_q_cardio_consultant = self.env.now
            with self.cardio_consultant.request() as req:
                yield req
                end_q_cardio_consultant = self.env.now
                #print ("Patient being seen on cardio PTWR")
                # need to consider changing this to log normal
                patient.q_time_cardio_consultant = end_q_cardio_consultant - start_q_cardio_consultant
                sampled_cardio_consultant_time = random.expovariate (1.0/ g.mean_cardio_consultant_time)

                # Decision to admit
                admission_probability = g.prob_cardio_admit 
                if random.random() < admission_probability:
                    # Patient is admitted
                    patient.disposition = "admitted"
                    #decision_to_admit_time = self.env.now - patient.start_time
                else:
                    # Patient is discharged
                    patient.disposition = "discharged"

                yield self.env.timeout(sampled_cardio_consultant_time)

        else: # see a medical consultant 
            
            start_q_medical_consultant = self.env.now
            with self.medical_consultant.request() as req:
                yield req
                end_q_medical_consultant = self.env.now
                #print ("Patient being seen on medical PTWR")
                # need to consider changing this to log normal
                patient.q_time_medical_consultant = end_q_medical_consultant - start_q_medical_consultant
                sampled_medical_consultant_time = random.expovariate (1.0/ g.mean_medical_consultant_time)

                # Decision to admit
                admission_probability = g.prob_medical_admit 
                if random.random() < admission_probability:
                    # Patient is admitted
                    patient.disposition = "admitted"
                    #decision_to_admit_time = self.env.now - patient.start_time
                else:
                    # Patient is discharged
                    patient.disposition = "discharged"

                yield self.env.timeout(sampled_medical_consultant_time)
        
        # timestamp for admission decision 
        decision_to_admit_time = self.env.now - patient.start_time

        # time_in_dept - calculate how long patient in dept in total
        total_time_ed = self.env.now - patient.start_time

        # record outputs
        self.results_df.loc[len(self.results_df)] = {
            "Patient ID": patient.id,
            "Patient Route": patient_route,
            "Q Time Take Doctor": patient.q_time_take_doctor,
            #"Number of Patients Clerked":
            "Time with Take Doctor": sampled_take_doctor_time,
            "Time for Ix": ix_time,
            "Type of PTWR": patient.flow,
            #"Number of Patients seen by Cardio":
            #"Number of Patients seen by Medicine": 
            "Q Time Cardio Consultant": getattr(patient, "q_time_cardio_consultant", 0.0),
            "Q Time Medical Consultant": getattr(patient, "q_time_medical_consultant", 0.0),
            "Time with Cardio Consultant": sampled_cardio_consultant_time if patient.flow == "cardio" else 0.0,
            "Time with Medical Consultant": sampled_medical_consultant_time if patient.flow == "medical" else 0.0,
            "Disposition Time": decision_to_admit_time,
            "Patient Disposition": patient.disposition,
            "Total Journey Time": total_time_ed

    def calculate_run_result (self):
        self.mean_q_time_nurse = self.results_df["Q Time Nurse"].mean()
        self.mean_q_time_take_doctor = self.results_df["Q Time Take Doctor"].mean()
        self.mean_q_time_cardio_consultant = self.results_df["Q Time Cardio Consultant"].mean()
        self.mean_q_time_medical_consultant = self.results_df["Q Time Medical Consultant"].mean()
        self.mean_journey_time = self.results_df["Total Journey Time"].mean()
        #self.mean_time_in_dept = 

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
            "Average No Patients seen by Medicine", "Mean Q Time Cardio Consultant",
            "Mean Q Time Medical Consultant", "Mean Journey Time"
        ])

    # print and record trial results
    def print_trial_results(self):
        print ("Trial Results")
        print (self.df_trial_results)
        # need to save to a PDF or table here 

    #run the trial!
    def run_trial(self):
        for run in range(g.number_of_runs):
            ed_med_expect_model = ED_Med_Expect_Model(run)
            ed_med_expect_model.run ()

            self.df_trial_results.loc[len(self.df_trial_results)] = {
                "Run Number": run,
                "Mean Q Time Nurse": ed_med_expect_model.mean_q_time_nurse,
                #"Average Patients per Run":
                #"Average No Patients Clerked":
                "Mean Q Time Take Doctor": ed_med_expect_model.mean_q_time_take_doctor,
                #"Average No Patients seen by Cardio":
                #"Average No Patients seen by Medicine":
                "Mean Q Time Cardio Consultant": ed_med_expect_model.mean_q_time_cardio_consultant,
                "Mean Q Time Medical Consultant": ed_med_expect_model.mean_q_time_medical_consultant,
                "Mean Journey Time": ed_med_expect_model.mean_journey_time
            }
        self.print_trial_results()

print ("Testing 123")

trial_1 = Trial ()
trial_1.run_trial()
