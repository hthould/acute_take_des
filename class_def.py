from timing import check_take_doctor_numbers

class g:
    # patient arrivals 
    sdec_patient_inter = 30
    ed_patient_inter = 30
    ed_med_expect_inter = 90

    # consult times 
    min_nurse_time = 15
    min_doctor_time = 60
    min_consultant_time = 10 
    min_ix_time = 45
    min_ed_ix_time = 30 
    min_amu_occupancy_time = 480

    mean_nurse_time = 10
    mean_sdec_doctor_time = 30 # need to edit this for different grades
    mean_take_doctor_time = 30 # need to edit this for different grades
    mean_consultant_time = 10
    mean_cardio_consultant_time = 10
    mean_medical_consultant_time = 10
    mean_sdec_ix_time = 60
    mean_ed_ix_time = 20
    mean_ed_med_expect_ix_time = 60
    mean_amu_bed_occupancy_time = 720

    # opening times
    sdec_open = 10
    sdec_closed = 19

    #sdec_day_open = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    #sdec_day_closed = ["Saturday", "Sunday"] 

    # staff availability 
    cardio_start = 9
    cardio_finish = 11
    sdec_consultant_start = 11
    sdec_consultant_finish = 19
    consultant_start = 8
    consultant_finish = 20

    #resources
    number_of_nurses = 4
    number_of_sdec_doctors = 2
    number_of_take_doctors = 2
    number_of_sdec_consultants = 1
    number_of_acute_med_consultants = 1
    number_of_pod_consultants = 1
    number_of_cardio_consultants = 1
    number_of_sdec_cubicles = 10 
    number_of_amu_beds = 55 # A400 + A515
    number_of_amu_beds_with_boarding = 34

    # probabilities
    sdec_probability = 0.4
    ed_probability = 0.4
    ed_med_expect_probability = 0.2
    prob_doctor_discharge = 0.1
    prob_sdec_admit = 0.4
    prob_cardio_admit = 0.8
    prob_medical_admit = 0.95
    prob_medical_expect_admit = 0.95
    prob_needs_cardioptwr = 0.1

    #sim meta data 
    warm_up_period = 10080 # 7 day warm up period 
    trial_period = 10080 # 7 day run 
    sim_duration = warm_up_period + trial_period
    number_of_runs = 3

# patient class (represents patients coming into acute services)
# add patient news score, age, frailty score 

class Patient: 
    def __init__(self, patient_id):
        self.id = patient_id
        self.start_time = 0
        self.q_time_nurse = 0
        self.q_sdec_bed = 0 
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
        self.admission_prob = 0
        self.aw_cardio_ptwr_count = 0 
        self.admit_aw_ptwr_count = 0 
        self.nurse_timestamp = 0
        self.doctor_timestamp = 0
        self.consultant_timestamp = 0 
       #self.news_score
       #self.frailty
       #self.age 
       #self.confused
       #self.needs_iv_therapy 
       #self.priority (need some logic with news)


