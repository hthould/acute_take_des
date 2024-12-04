import pandas as pd
import simpy
import random

from class_def import g 
from class_def import Patient

# model
class ED_Model: 

    # constructor 
    def __init__(self, run_number):
        self.env = simpy.Environment()
        self.patient_counter = 0 # used as a patient ID

        # resources
        self.take_doctor = simpy.Resource (self.env, 
            capacity = g.number_of_take_doctors)
        self.medical_consultant = simpy.Resource (self.env, 
            capacity = g.number_of_medical_consultants)
        self.cardio_consultant = simpy.Resource (self.env, 
            capacity = g.number_of_cardio_consultants)
        self.run_number = run_number 

        #set dataframe to record results
        self.results_df = pd.DataFrame(columns = ["Patient ID", "Patient Route","Q Time Take Doctor",
                                                  "Time with Take Doctor", "Time for Ix",
                                                  "Type of PTWR", "Q Time Cardio Consultant", 
                                                  "Q Time Medical Consultant", 
                                                  "Time with Cardio Consultant", 
                                                  "Time with Medical Consultant", 
                                                  "Total Journey Time" ])
        self.results_df.set_index("Patient ID", inplace=True)

        # set starting values
        self.mean_q_time_take_doctor = 0
        self.mean_q_time_cardio_consultant = 0
        self.mean_q_time_medical_consultant = 0

        sampled_cardio_consultant_time = 0
        sampled_medical_consultant_time = 0

        print ("Passed the constructor")

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

            print ("Patient arrived")

    # generator function to pass through medical take 
    def ed_medical_take (self, patient):

        # log that patient attended ED into Patient Route 
        patient_route = "ED"

        print ("Patient arrived in ED")

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
        
        print ("Patient has been clerked")

        # Assign PTWR status here - cardio vs medical
        patient.flow = "cardio" if random.random() < g.prob_needs_cardioptwr else "medical"


        # investigation sink
        ix_time = random.expovariate(1.0 / g.mean_ed_ix_time)
        patient.ix_time = ix_time
        yield self.env.timeout(ix_time)

        print ("Investigations complete")

        # PTWR process: can either see a cardiology consultant or a medical consultant

        if  patient.flow == "cardio":

            # cardio PTWR only happens at 0900 each day 
            start_q_cardio_consultant = self.env.now
            with self.cardio_consultant.request() as req:
                yield req
                end_q_cardio_consultant = self.env.now
                print ("Patient being seen on cardio PTWR")
                # need to consider changing this to log normal
                patient.q_time_cardio_consultant = end_q_cardio_consultant - start_q_cardio_consultant
                sampled_cardio_consultant_time = random.expovariate (1.0/ g.mean_cardio_consultant_time)
                yield self.env.timeout(sampled_cardio_consultant_time)

        else: # see a medical consultant 
            
            start_q_medical_consultant = self.env.now
            with self.medical_consultant.request() as req:
                yield req
                end_q_medical_consultant = self.env.now
                print ("Patient being seen on medical PTWR")
                # need to consider changing this to log normal
                patient.q_time_medical_consultant = end_q_medical_consultant - start_q_medical_consultant
                sampled_medical_consultant_time = random.expovariate (1.0/ g.mean_medical_consultant_time)
                yield self.env.timeout(sampled_medical_consultant_time)

        # time_in_dept - calculate how long patient in dept in total
        total_time = self.env.now - patient.start_time

        # record outputs
        self.results_df.loc[len(self.results_df)] = {
            "Patient ID": patient.id,
            "Patient Route": patient_route,
            "Q Time Take Doctor": patient.q_time_take_doctor,
            "Time with Take Doctor": sampled_take_doctor_time,
            "Time for Ix": ix_time,
            "Type of PTWR": patient.flow,
            "Q Time Cardio Consultant": getattr(patient, "q_time_cardio_consultant", 0.0),
            "Q Time Medical Consultant": getattr(patient, "q_time_medical_consultant", 0.0),
            "Time with Cardio Consultant": sampled_cardio_consultant_time if patient.flow == "cardio" else 0.0,
            "Time with Medical Consultant": sampled_medical_consultant_time if patient.flow == "medical" else 0.0,
            "Total Journey Time": total_time
        }
    '''
        if patient.flow == "cardio":
            self.results_df.loc[len(self.results_df)] = {
            "Q Time Cardio Consultant": patient.q_time_cardio_consultant,
            "Time with Cardio Consultant": sampled_cardio_consultant_time}

        else:
            self.results_df.loc[len(self.results_df)] = {
            "Q Time Medical Consultant": patient.q_time_medical_consultant,
             "Time with Medical Consultant": sampled_medical_consultant_time}'''

    def calculate_run_result (self):
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
    
    # admitted or discharged

    # await for medical bed 

#Trial class
class Trial:

    # dataframe for trial results 
    def  __init__(self):
        self.df_trial_results = pd.DataFrame(columns=[
            "Run Number","Mean Q Time Take Doctor","Mean Q Time Cardio Consultant", 
            "Mean Q Time Medical Consultant","Mean Journey Time"
        ])

    # print and record trial results
    def print_trial_results(self):
        print ("Trial Results")
        print (self.df_trial_results)
        # need to save to a PDF or table here 

    #run the trial!
    def run_trial(self):
        for run in range(g.number_of_runs):
            ed_model = ED_Model(run)
            ed_model.run ()

            self.df_trial_results.loc[len(self.df_trial_results)] = {
                "Run Number": run,
                "Mean Q Time Take Doctor": ed_model.mean_q_time_take_doctor,
                "Mean Q Time Cardio Consultant": ed_model.mean_q_time_cardio_consultant,
                "Mean Q Time Medical Consultant": ed_model.mean_q_time_medical_consultant,
                "Mean Journey Time": ed_model.mean_journey_time
            }
        self.print_trial_results()

print ("Testing 123")

trial_1 = Trial ()
trial_1.run_trial()

