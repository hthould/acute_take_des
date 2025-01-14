# import necessary packages 
import simpy 
import pandas as pd 
import random

# create functions for the relevant objects 

# global parameter model
class g:
    time_between_patient_referral = 30
    av_nurse_rv_time = 20 
    av_post_nurse_ix_time = 60
    av_resident_rv_time = 126
    av_post_resident_ix_time = 30 
    number_of_nurses = 4
   # number_of_cubicles = 14 - not yet coded - not seen as significant holding
        # point on initial modelling 
    number_of_doctors = 6
    sim_duration = 2880
    number_of_runs = 10 

# entity class

class Patient:
    def__init__(self, p_id):
        self.id = p_id
        self.time_to_posttake = 0 

# model class 

class Model:

    # constructor function
    def __init__ (self, run_number):
        self.env = simpy.Environment()
        self.patient_counter= 0 
        self.nurse = simpy.Resource(self.env, capacity = number_of_nurses)
        self.doctor = simpy.Resource(self.env, capacity = number_of_doctors)
        self.run_number = run_number

        # create a Pandas dataframe to store results 
        self.results_df = pd.DataFrame()
        self.results_df ["Patient ID"] = [1]
        self.results_df ["Queue time for nurse"]
        self.results_df ["Time with nurse"]
        self.results_df ["Queue time for doctor"]
        self.results_df ["Time with doctor"]
        self.results_df ["Time to PTWR"] = [0.0]
        self.results_df.set_index ("Patient ID", inplace=True)

        ''' This needs looking at!!'''

    # generator function (patient arrivals - who, how and how often)
    def generator_patient_arrival (self):
        while True:
            self.patient_counter += 1
            p = Patient (self.patient_counter)
            self.env.process (self.medical_take (p))
            # randomly sample a time to next customer arriving using lamba 
            # 1/mean and an expotential distribution
            sampled_inter_arrival_time = random.expovariate(1.0/g.time_between_patient_referral)
            yield self.env.timeout(sampled_inter_arrival_time)
    
    # function to model the take: patient arrives, waits to see a nurse, is 
    # seen, waits for ix, waits for a doctor, is seen, waits for further 
    # investigations before being ready for the PTWR
    def medical_take (self, patient):

        #see the nurse
        start_q_nurse = self.env.now
        with self.nurse.request() as req:
            yield req
            end_q_nurse = self.env.now
            patient.queue_time_nurse =  end_q_nurse - start_q_nurse
            sampled_time_with_nurse = random.expovariate(1.0/g.av_nurse_rv_time)
            self.results_df.at[patient.id, "Queue time for nurse"] = (
                patient.queue_time_nurse)
            self.results_df.at[patient.id, "Time with nurse"] = (
                patient.sampled_time_with_nurse)
            yield self.env.timeout(sampled_time_with_nurse)
        
        # insert a temporary sink here to model waiting for results 

        # see the resident doctor 
        start_q_doctor = self.env.now
        with self.doctor.request() as req:
            yield req
            end_q_doctor = self.env.now 
             patient.queue_time_doctor =  end_q_doctor - start_q_doctor
            sampled_time_with_doctor = random.expovariate(1.0/g.av_resident_rv_time)
            self.results_df.at[patient.id, "Queue time for doctor"] = (
                patient.queue_time_doctor)
            self.results_df.at[patient.id, "Time with doctor"] = (
                patient.sampled_time_with_doctor)
            yield self.env.timeout(sampled_time_with_doctor)

        # another temporary sink here to represent further investigations 

        time_to_PTWR = start_q_nurse - end_q_doctor
        self.results_df.at[patient.id, "Time to PTWR"] = (
            patient.time_to_PTWR) 

    # calculate the run results 
    def calculate_run_results(self):
        self.mean_queue_time_nurse = self.results_df["Time with nurse"].mean()
        self.mean_queue_time_doctor = self.results_df["Time with doctor"].mean()
        self.mean_time_to_PTWR = self.results_df["Time to PTWR"].mean()
        self.min_time_to_PTWR = self.results_df["Time to PTWR"].min()
        self.max_time_to_PTWR = self.results_df["Time to PTWR"].max()

    def run(self):
        self.env.process(self.generator_patient_arrival())
        self.env.run(until = g.sim_duration)
        self.calculate_run_results()

        print (f"Run number {self.run_number}")
        print (self.results_df)

# trial class 

class Trial:

    def __init__ (self):
        self.df_trial_results = pd.DataFrame()
        self.df_trial_results ["Run Number"] = [0]
        self.df_trial_results ["Mean time with nurse"] = [0.0]
        self.df_trial_results ["Mean time with doctor"] = [0.0]
        self.df_trial_results ["Mean time to PTWR"] = [0.0]
        self.df_trial_results ["Min time to PTWR"] = [0.0]
        self.df_trial_results ["Max time to PTWR"] = [0.0]
        self.df_trial_results.set_index ("Run Number", inplace = True)

    # Need to create a method to take the mean over the runs to get average 
    # predicted queueing times 

    def print_trial_results(self):
        print ("Trial Results")
        print (self.df_trial_results)
    
     # need to save the results to a csv file
    
    def run_trials (self):
        for run in range (g.number_of_runs):
            my_model = Model (run)
            my_model.run()

            self.df_trial_results.loc[run] = [my_model.mean_queue_time_nurse]
            self.df_trial_results.loc[run] = [my_model.mean_queue_time_doctor]
            self.df_trial_results.loc[run] = [my_model.mean_time_to_PTWR]
            self.df_trial_results.loc[run] = [my_model.min_time_to_PTWR]
            self.df_trial_results.loc[run] = [my_model.max_time_to_PTWR]

            self.print_trial_results()