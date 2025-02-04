import pandas as pd
import simpy
import random
import streamlit as st 

#streamlit app set up 
st.set_page_config(layout="wide")

from class_def import g
from timing import calculate_hour_of_day, calculate_day_of_week, extract_hour
from timing import get_consultant_patient_count, get_doctor_patient_count, check_take_doctor_numbers
from medical_take_model import Trial



# title 
st.title ("Medical Take discrete event simulation")

st.divider ()

tab1, tab2, tab3 = st.tabs(["Info", "Results", "Results table"])

#sidebar for inputs 
with st.sidebar:
    
    # sliders to change input parameters 
    st.header ("Alter input parameters here")

    st.divider()

    st.write ("Press the button below if you would like to run the simulation acccording"
              " to the current rota")
    run_as_timetable = st.button ("Rota numbers")
    #if run_as_timetable:

    st.divider()

    st.write("If you'd like to alter any of the staffing numbers, do so using the sliders below")

    sdec_doctors_slider = st.slider("Number of SDEC doctors", min_value= 2, max_value= 5, value= 2)
    take_doctors_slider = st.slider("Number of take doctors", min_value= 2, max_value= 10, value= 4)
    sdec_consultants_slider = st.slider("Number of SDEC consultants", min_value= 0, max_value= 5, value= 1)
    acute_med_consultants_slider = st.slider("Number of acute med consultants", min_value= 0, max_value= 5, value= 1)
    pod_consultants_slider = st.slider("Number of POD consultants", min_value= 0, max_value= 5, value= 1)
    cardio_consultants_slider = st.slider("Number of cardio consultants", min_value= 0, max_value= 5, value= 1)

    st.divider()
        
    st.write ("Use the sliders below to change SDECs opening times")
    sdec_open_slider = st.slider("SDEC opening time", min_value= 8, max_value= 12, value= 10)
    sdec_closed_slider = st.slider("SDEC closing time", min_value= 16, max_value= 24, value= 19)

    st.write ("Press the button below to adjust SDEC weekend hours")
    sdec_saturday = st.button ("Open SDEC on Saturday")
    sdec_sunday = st.button("Open SDEC on Sunday")

    st.divider()

    st.write ("Use the sliders below to change the number of cubicles or bed spaces")
    sdec_cubicles_slider = st.slider("Number of SDEC cubicles", min_value= 5, max_value= 20, value= 10)
    amu_beds_slider = st.slider("Number of AMU beds", min_value= 10, max_value= 50, value= 30)

    # carry the slider inputs into the g class 
    g.number_of_sdec_doctors = sdec_doctors_slider
    g.number_of_take_doctors = take_doctors_slider
    g.number_of_sdec_consultants = sdec_consultants_slider
    g.number_of_acute_med_consultants = acute_med_consultants_slider
    g.number_of_pod_consultants = pod_consultants_slider
    g.number_of_cardio_consultants = cardio_consultants_slider
    g.sdec_open = sdec_open_slider
    g.sdec_closed = sdec_closed_slider
    g.number_of_sdec_cubicles = sdec_cubicles_slider
    g.number_of_amu_beds = amu_beds_slider

    button_run_pressed = st.button("Run simulation")

# first tab for introduction
with tab1:

    st.write ("This discrete event simulation (DES) is designed to model the take process."
          " In this process, a patient is either referred to the hospital by primary care,"
          " be that a GP or a paramedic, or by ED and is then seen in either SDEC or"
          " in ED, depending on referral source and patient acuity. Once seen by a resident"
          " doctor, they are then seen by a consultant and either discharged or"
          " listed for a medical bed. This DES aims to demonstrate the impact of SDEC and ED"
          " bed capacity, staffing numbers, and SDEC availability, on patient flow"
          " through the medical take.")
    
    st.write ("By changing the parameters located in the side bar to the left of the screen"
              " you will be able to assess the effect of different staffing numbers, bed spaces"
               " and SDEC opening times on patient flow.")


# third tab for results table 
with tab3:

    if button_run_pressed:
        results_df = Trial().run_trial()
        st.dataframe(results_df)

    st.button ("Click here to download the results into a PDF")
