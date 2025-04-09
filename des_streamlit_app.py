import pandas as pd
import simpy
import random
import streamlit as st 
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import plotly.express as px 

#streamlit app set up 
st.set_page_config(layout="wide")

from class_def import g
from timing import calculate_hour_of_day, calculate_day_of_week, extract_hour
from timing import get_consultant_patient_count, get_doctor_patient_count, check_take_doctor_numbers
from medical_take_model import Trial, Model



# title 
st.title ("Medical Take discrete event simulation")

st.divider ()

tab1, tab2, tab3, tab4 = st.tabs(["Info", "Results", "Metrics", "Results table"])

#sidebar for inputs 
with st.sidebar:
    
    # sliders to change input parameters 
    st.header ("Alter input parameters here")

    st.divider()

    trial_length_slider = st.slider ("How many days would you like to run the simulation for?", min_value = 1, max_value = 14, value = 3)

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

    st.write ("Use the slider below to choose how many days a week SDEC is open")
    sdec_day_slider = st.slider ("Number of days a week SDEC is staffed", min_value = 1, max_value = 7, value = 5)

    st.divider()

    st.write ("Use the sliders below to change the number of cubicles or bed spaces")
    sdec_cubicles_slider = st.slider("Number of SDEC cubicles", min_value= 5, max_value= 20, value= 10)
    amu_beds_slider = st.slider("Number of AMU beds", min_value= 10, max_value= 50, value= 30)

    # carry the slider inputs into the g class 
    g.trial_period = trial_length_slider * 1440
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

    st.image("take_process_map.png", caption = "UHBW Medical Take Process Map")
    
    st.write ("By changing the parameters located in the side bar to the left of the screen"
              " you will be able to assess the effect of different staffing numbers, bed spaces"
               " and SDEC opening times on patient flow.")

# second tab for charts 
with tab2:

    if button_run_pressed:

        # graph to represent time to admission decision
        results = pd.read_csv ("/Users/hannah/Documents/Medicine/Chief Registrar/acute_take_des/results.csv")
        results = results.sort_values (by = "Start Time")

        fig_time_1 = px.line (results, 
                       x = "Start Time in Days", 
                       y = "Journey Time: Admission to Disposition (h)",
                       color = "Run ID",
                       title = "Time until Decision To Admit (DTA)"
                       )
        
        median_value = results['Journey Time: Admission to Disposition (h)'].median()

        fig_time_1.update_yaxes(range=[0, 12])
        fig_time_1.add_hline(y=median_value, 
              line_dash="dash", 
              line_color="yellow", 
              annotation_text=f"Median: {median_value:.2f}",
              annotation_position="top left")
        
        st.plotly_chart (fig_time_1)
        
        # graph to demonstrate queue times 

        # Need to melt the dataframe to be able to plot different Q times as colour categories 
        melted_results = results.melt (id_vars = ["Start Time in Days"],
                                       value_vars = ["Q Time Nurse", "Q Time Doctor", "Q Time Consultant"],
                                       var_name = "Queue Type",
                                       value_name = "Queue Time (mins)")
        
        fig_queue = px.histogram (melted_results,
                            x = "Start Time in Days",
                            y = "Queue Time (mins)",
                            color = "Queue Type",
                            title = "Clinical Queue Times over Time"
                            )
        st.plotly_chart (fig_queue)

        # graph to demonstrate queue time for a bed (from disposition)

        fig_queue_bed = px.histogram (results,
                                 x = "Start Time in Days",
                                 y = "Q Time AMU Bed",
                                 color = "Run ID",
                                 title = "AMU Bed Waits",
                                 )
        st.plotly_chart (fig_queue_bed)

        # graph to show patient location over time (SDEC, ED, AMU)


                         
# third tab for metrics and dials

with tab3:

    if button_run_pressed:
        st.write ("Filler xyz")   

# fourth tab for results table 
with tab4:

    if button_run_pressed:
        results_df = Trial().run_trial()
        st.dataframe(results_df)

        #pdf_name = st.text_input ("Type in a name for your PDF file")

        pdf_button =  st.button ("Click here to download the results into a PDF")

        if pdf_button:
            def df_to_pdf(results_df, filename="output.pdf"):
                #pdf_name = st.text_input ("Type in a name for your PDF file")

                pdf = canvas.Canvas(filename, pagesize=letter) 
                width, height = letter

                # Convert DataFrame to list of lists (including headers)
                table_data = [results_df.columns.to_list()] + results_df.values.tolist()
                
                # Create Table
                table = Table(table_data)
                
                # Add Styling
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ])
                table.setStyle(style)

                # Position Table in the PDF
                table.wrapOn(pdf, width, height)
                table.drawOn(pdf, 50, height - 200)  # Adjust positioning

                pdf.save()
                print(f"PDF saved as {filename}")

            # Convert DataFrame to PDF
            df_to_pdf(results_df, "dataframe_output.pdf")

