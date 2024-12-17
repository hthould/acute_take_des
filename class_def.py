
class g:
    # patient arrivals 
    sdec_patient_inter = 30
    ed_patient_inter = 30
    ed_med_expect_inter = 90

    # consult times 
    mean_nurse_time = 20
    mean_doctor_time = 60 # need to edit this for different grades
    mean_take_doctor_time = 60 # need to edit this for different grades
    mean_consultant_time = 20
    mean_cardio_consultant_time = 20
    mean_medical_consultant_time = 20
    mean_sdec_ix_time = 90
    mean_ed_ix_time = 30

    #resources
    number_of_nurses = 4
    number_of_doctors = 2
    number_of_take_doctors = 4
    number_of_consultants = 1
    number_of_medical_consultants = 1
    number_of_cardio_consultants = 1

    # probabilities
    prob_doctor_discharge = 0.1
    prob_consultant_discharge = 0.6
    prob_needs_cardioptwr = 0.1

    #sim meta data 
    warm_up_period = 1440 # 24 hour warm up period 
    trial_period = 2880 # 2 days 
    sim_duration = warm_up_period + trial_period
    number_of_runs = 3

# patient class (represents patients coming into acute services)
# add patient news score, age, frailty score 

class Patient: 
    def __init__(self, patient_id):
        self.id = patient_id
        self.start_time = 0
        self.q_time_nurse = 0
        self.q_time_doctor = 0 
        self.q_time_take_doctor = 0
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


