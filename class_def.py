
class g:
    # patient arrivals 
    sdec_patient_inter = 30
    ed_patient_inter = 30
    ed_med_expect_inter = 90

    # consult times 
    min_nurse_time = 10
    min_doctor_time = 40
    min_consultant_time = 10 
    min_ix_time = 30
    min_ed_ix_time = 10 
    min_amu_occupancy_time = 1440

    mean_nurse_time = 10
    mean_sdec_doctor_time = 30 # need to edit this for different grades
    mean_take_doctor_time = 30 # need to edit this for different grades
    mean_consultant_time = 10
    mean_cardio_consultant_time = 10
    mean_medical_consultant_time = 10
    mean_sdec_ix_time = 60
    mean_ed_ix_time = 20
    mean_ed_med_expect_ix_time = 60
    mean_amu_bed_occupancy_time = 1440

    # opening times
    sdec_open = 10
    sdec_closed = 19

    # staff availability 
    cardio_start = 9
    cardio_finish = 11

    #resources
    number_of_nurses = 4
    number_of_sdec_doctors = 2
    number_of_take_doctors = 3
    number_of_sdec_consultants = 1
    number_of_acute_med_consultants = 1
    number_of_pod_consultants = 1
    number_of_cardio_consultants = 1
    number_of_sdec_cubicles = 10 
    number_of_amu_beds = 30
    number_of_amu_beds_with_boarding = 34

    # probabilities
    sdec_probability = 0.4
    ed_probability = 0.4
    ed_med_expect_probability = 0.2
    prob_doctor_discharge = 0.1
    prob_sdec_admit = 0.3
    prob_cardio_admit = 0.8
    prob_medical_admit = 0.95
    prob_medical_expect_admit = 0.95
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
        self.q_time_bed = 0
        self.bed_allocation= 0 
        self.ix_time = 0
        self.total_time_in_dept = 0
        self.disposition = None
        self.decision_to_admit_time = 0 
        self.time_patient_got_bed = 0
        self.doctor_type = None
        self.consultant_type = None
       #self.news_score
       #self.frailty
       #self.age 
       #self.confused
       #self.needs_iv_therapy 
       #self.priority (need some logic with news)


