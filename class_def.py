
class g:
    # patient arrivals 
    patient_inter = 30

    # consult times 
    mean_nurse_time = 20
    mean_doctor_time = 60 # need to edit this for different grades
    mean_consultant_time = 20
    mean_sdec_ix_time = 90
    mean_ed_ix_time = 30

    #resources
    number_of_nurses = 4
    number_of_doctors = 2
    number_of_consultants = 1
    number_of_cardio_consultants = 1

    # probabilities
    prob_doctor_discharge = 0.1
    prob_consultant_discharge = 0.8

    #sim meta data 
    warm_up_period = 1440 # 24 hour warm up period 
    trial_period = 2880 # 2 days 
    sim_duration = warm_up_period + trial_period
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
        self.q_time_medical_consultant = 0
        self.q_time_cardio_consultant = 0
        self.ix_time = 0
       #self.news_score
       #self.frailty
       #self.age 
       #self.confused
       #self.needs_iv_therapy 
       #self.priority (need some logic with news)


