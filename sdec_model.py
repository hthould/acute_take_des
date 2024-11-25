import pandas as pd
import simpy
import random

# g class (stores global parameters)

class g:
    patient_inter = 30
    mean_nurse_time = 20
    mean_doctor_time = 60 # need to edit this for different grades
    mean_consultant_time = 20
    number_of_nurses = 4
    number_of_doctors = 2
    number_of_consultants = 1
    sim_duration = 600
    number_of_runs = 5

# patient class (represents patients coming into acute services)
# add patient news score, age, frailty score 

class Patient: 
    def __init__(self, patient_id):
        self.id = patient_id
        self.start_time = 0
        self.q_time_nurse = 0
        self.q_time_doctor = 0 
        self.q_time_consultant = 0
        self.ix_time = 0
       #self.news_score
       #self.frailty
       #self.age 
       #self.confused
       #self.needs_iv_therapy 
       #self.priority (need some logic with news)

# model class
class Model: 

    # constructor 
    def __init__(self, run_number):
        self.env = simpy.Environment()
        self.patient_counter = 0 # used as a patient ID

        # resources
        self.nurse = simpy.Resource (self.env, 
            capacity = g.number_of_nurses)
        self.doctor = simpy.Resource (self.env, 
            capacity = g.number_of_doctors)
        self.consultant = simpy.Resource (self.env, 
            capacity = g.number_of_consultants)
        self.run_number = run_number 
        #self.results_df = pd.DataFrame (columns= [
           # "Patient ID", "Q Time Nurse", "Time with Nurse",
           # "Q Time Doctor", "Time with Doctor",
           # "Q Time Consultant", "Time with Consultant", "Total Journey Time"])

        self.results_df = pd.DataFrame()
        self.results_df["Patient ID"] = [1]
        self.results_df["Q Time Nurse"] = [0.0]
        self.results_df["Time with Nurse"] = [0.0]
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
            self.env.process (self.attend_hospital (p))
            #randomly sample time to patient arrival
            sampled_inter = random.expovariate (1.0/ g.patient_inter)
            yield self.env.timeout (sampled_inter)
    
    # generator function to pass through medical take 
    def attend_hospital (self, patient):

    # need to add a differentiator so there is a pathway for ED and SDEC with 
    # a proportion of patients passing down each pathway 

        # nurse process 
        start_q_nurse = self.env.now
        with self.nurse.request() as req:
            yield req
            end_q_nurse = self.env.now
            # need to consider changing this to log normal
            patient.q_time_nurse = end_q_nurse - start_q_nurse
            sampled_nurse_time = random.expovariate (1.0/ g.mean_nurse_time)
            yield self.env.timeout(sampled_nurse_time)

        # doctor process 
        start_q_doctor = self.env.now
        with self.doctor.request() as req:
            yield req
            end_q_doctor = self.env.now
            # need to consider changing this to log normal
            patient.q_time_doctor = end_q_doctor - start_q_doctor
            sampled_doctor_time = random.expovariate (1.0/ g.mean_doctor_time)
            yield self.env.timeout(sampled_doctor_time)

        # investigation sink
        ix_time = random.expovariate(1.0 / 90)
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
        
        # could include a proportion of patients discharged pre-PTWR as a proportion

    def calculate_run_result (self):
        self.mean_q_time_nurse = self.results_df["Q Time Nurse"].mean()
        self.mean_q_time_doctor = self.results_df["Q Time Doctor"].mean()
        self.mean_q_time_consultant = self.results_df["Q Time Consultant"].mean()
        self.mean_journey_time = self.results_df["Total Journey Time"].mean()
        #self.mean_time_in_dept = 
    
    def run (self):
        self.env.process(self.generator_patient_arrival())
        self.env.run(until = g.sim_duration)
        self.calculate_run_result()

        print (f"Run Number {self.run_number}")
        print (self.results_df)
    
#print ("Testing 123")

#Trial class
class Trial:

    # dataframe for trial results 
    def  __init__(self):
        self.df_trial_results = pd.DataFrame(columns=[
            "Run Number", "Mean Q Time Nurse", "Mean Q Time Doctor",
              "Mean Q Time Consultant", "Mean Journey Time"
        ])

    # print and record trial results
    def print_trial_results(self):
        print ("Trial Results")
        print (self.df_trial_results)
        # need to save to a PDF or table here 

    #run the trial!
    def run_trial(self):
        for run in range(g.number_of_runs):
            sdec_model = Model(run)
            sdec_model.run ()

            self.df_trial_results.loc[len(self.df_trial_results)] = {
                "Run Number": run,
                "Mean Q Time Nurse": sdec_model.mean_q_time_nurse,
                "Mean Q Time Doctor": sdec_model.mean_q_time_doctor,
                "Mean Q Time Consultant": sdec_model.mean_q_time_consultant,
                "Mean Journey Time": sdec_model.mean_journey_time
            }
        self.print_trial_results()

print ("Testing 123")

trial_1 = Trial ()
trial_1.run_trial()
