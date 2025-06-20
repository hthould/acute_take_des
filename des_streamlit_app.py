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
import os
import glob
import plotly.graph_objects as go

#streamlit app set up 
st.set_page_config(layout="wide")

from class_def import g
from timing import calculate_hour_of_day, calculate_day_of_week, extract_hour
from timing import get_consultant_patient_count, get_doctor_patient_count, check_take_doctor_numbers
#from medical_take_model import Trial, Model
from temp_des import Trial, Model

# title 
st.title ("Medical Take discrete event simulation")

st.divider ()

tab1, tab2, tab3, tab4 = st.tabs(["How to use me", "Background", "Results", "Results table"])

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

# first tab for how to use me 
with tab1:

    st.write ("This discrete event simulation (DES) is designed to model the take process.")

    st.write ("By changing the parameters located in the side bar to the left of the screen"
              " you will be able to assess the effect of different staffing numbers, bed spaces"
               " and SDEC opening times on patient flow.")
    st.write ("Important info: This is an unvalidated model and incorporates a number of significant assumptions.")


# second tab for introduction and background
with tab2:

    st.write (" In this process, a patient is either referred to the hospital by primary care,"
          " be that a GP or a paramedic, or by ED and is then seen in either SDEC or"
          " in ED, depending on referral source and patient acuity. Once seen by a resident"
          " doctor, they are then seen by a consultant and either discharged or"
          " listed for a medical bed.")
    
    st.write ("This DES aims to demonstrate the impact of SDEC and ED"
          " bed capacity, staffing numbers, and SDEC availability, on patient flow"
          " through the medical take.")

    st.image("take_process_map.png", caption = "UHBW Medical Take Process Map")

# third  tab for charts 
with tab3:

    # Use session state to remember if trial has been run
    if 'trial_ran' not in st.session_state:
        st.session_state.trial_ran = False

    # If button pressed, run trial and mark state
    if button_run_pressed:
        Trial().run_trial()
        st.session_state.trial_ran = True

    # Show results or waiting message
    if st.session_state.trial_ran:

        # graph to represent time to admission decision
        # from original calculated results 
        
         # Define the path pattern (adjust as needed)
        folder_path = "/Users/hannah/Documents/Medicine/Chief Registrar/acute_take_des/"
        pattern = os.path.join(folder_path, "results*.csv")

        # Get list of matching files
        files = glob.glob(pattern)

        # Check if any files match
        if files:
            # Get the most recently modified file
            latest_path = max(files, key=os.path.getmtime)

            # Read into DataFrame
            results = pd.read_csv(latest_path)
            print(f"Most recent file loaded: {latest_path}")
        else:
            print("No matching files found.")
            results = None  # Optional: so you don't reference undefined variable
        
        #results = pd.read_csv ("/Users/hannah/Documents/Medicine/Chief Registrar/acute_take_des/results.csv")
        results = results.sort_values (by = "Start Time")
        results['Run ID'] = results['Run ID'].astype(str)

        results_after_warm_up = results[results["Start Time in Days"] >= 7]
        results_after_warm_up['Run ID'] = results_after_warm_up['Run ID'].astype(str)

        fig_time_1 = px.scatter (results, 
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

        # Alternative datae source (event log)

        # Get the data for the graphs
        # Define the path pattern (adjust as needed)
        folder_path = "/Users/hannah/Documents/Medicine/Chief Registrar/acute_take_des/"
        pattern = os.path.join(folder_path, "combined_trial_output_*.csv")

        # Get list of matching files
        files = glob.glob(pattern)

        # Check if any files match
        if files:
            # Get the most recently modified file
            latest_path_1 = max(files, key=os.path.getmtime)

            # Read into DataFrame
            latest_file = pd.read_csv(latest_path_1)
            print(f"Most recent file loaded: {latest_path_1}")
        else:
            print("No matching files found.")
            latest_file = None  # Optional: so you don't reference undefined variable

        # create a dataframe with arrival time and disposition time 
        filtered_df_arriv_disp = latest_file[latest_file['Event'].isin(['Arrival to hospital', 'Patient Disposition'])][['Timestamp', 'Run ID', 'Event', 'Patient ID']]
        pivot_filtered_df_arriv_disp = filtered_df_arriv_disp.pivot(index=['Patient ID','Run ID'], columns='Event', values='Timestamp').reset_index()

        # Then calculate journey time 
        pivot_filtered_df_arriv_disp['Journey Time'] = pivot_filtered_df_arriv_disp['Patient Disposition'].astype(float) - pivot_filtered_df_arriv_disp['Arrival to hospital'].astype(float)

        # Sort by arrival time 
        pivot_filtered_df_arriv_disp = pivot_filtered_df_arriv_disp.sort_values(by= ['Arrival to hospital'])

        pivot_filtered_df_arriv_disp ['Arrival to hospital (days)'] = pivot_filtered_df_arriv_disp['Arrival to hospital'].astype(float) / 1440
        pivot_filtered_df_arriv_disp ['Journey Time (h)'] = pivot_filtered_df_arriv_disp ['Journey Time'].astype(float) / 60

        fig_time_a = px.scatter (pivot_filtered_df_arriv_disp, 
                       x = "Arrival to hospital (days)", 
                       y = "Journey Time (h)",
                       color = "Run ID",
                       title = "Time until Decision To Admit (DTA)",
                       )
        fig_time_a.update_traces(marker_size = 5)

        fig_time_a.add_hline(y=median_value, 
              line_dash="dash", 
              line_color="yellow", 
              annotation_text=f"Median: {median_value:.2f}",
              annotation_position="top left")
        
        st.plotly_chart(fig_time_a)

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

        # alternative data source (event log)

        # nurse queues
        filtered_df_queue_nurse = latest_file[latest_file['Event'].isin(['Arrival to hospital','Request Nurse', 'Nurse Start'])][['Timestamp', 'Run ID', 'Event', 'Patient ID']]
        pivot_filtered_df_queue_nurse = filtered_df_queue_nurse.pivot(index=['Patient ID','Run ID'], columns='Event', values='Timestamp').reset_index()
         # Then calculate queue time 
        pivot_filtered_df_queue_nurse['Queue Time'] = pivot_filtered_df_queue_nurse['Nurse Start'].astype(float) - pivot_filtered_df_queue_nurse['Request Nurse'].astype(float)
        pivot_filtered_df_queue_nurse['Queue Type'] = 'Nurse'
        # doctor queues
        filtered_df_queue_doctor = latest_file[latest_file['Event'].isin(['Arrival to hospital','Request Doctor', 'Doctor Start'])][['Timestamp', 'Run ID', 'Event', 'Patient ID']]
        pivot_filtered_df_queue_doctor = filtered_df_queue_doctor.pivot(index=['Patient ID','Run ID'], columns='Event', values='Timestamp').reset_index() 
         # Then calculate queue time 
        pivot_filtered_df_queue_doctor['Queue Time'] = pivot_filtered_df_queue_doctor['Doctor Start'].astype(float) - pivot_filtered_df_queue_doctor['Request Doctor'].astype(float)
        pivot_filtered_df_queue_doctor['Queue Type'] = 'Doctor'
        # consultant queues
        filtered_df_queue_consultant = latest_file[latest_file['Event'].isin(['Arrival to hospital','Request Consultant', 'Consultant Start'])][['Timestamp', 'Run ID', 'Event', 'Patient ID']]
        pivot_filtered_df_queue_consultant = filtered_df_queue_consultant.pivot(index=['Patient ID','Run ID'], columns='Event', values='Timestamp').reset_index()
         # Then calculate queue time 
        pivot_filtered_df_queue_consultant['Queue Time'] = pivot_filtered_df_queue_consultant['Consultant Start'].astype(float) - pivot_filtered_df_queue_consultant['Request Consultant'].astype(float)
        pivot_filtered_df_queue_consultant['Queue Type'] = 'Consultant'

        # combine to one dataframe
        # Merge nurse and doctor queues
        #combined_queue_df = pd.merge(
            #pivot_filtered_df_queue_nurse,
            #pivot_filtered_df_queue_doctor,
            #on=['Patient ID', 'Run ID'],
            #how='outer'
        #)


        # Then merge with consultant queues
        #combined_queue_df = pd.merge(
            #combined_queue_df,
            #pivot_filtered_df_queue_consultant,
            #on=['Patient ID', 'Run ID'],
            #how='outer'
        #)

        combined_queue_df = pd.concat([
            pivot_filtered_df_queue_nurse,
            pivot_filtered_df_queue_doctor,
            pivot_filtered_df_queue_consultant
            ], ignore_index=True)

        # convert the arrival to hospital time from units to days 
        combined_queue_df ['Arrival to hospital (days)'] = combined_queue_df ['Arrival to hospital'].astype(float) / 1440
        combined_queue_df['Queue Time (h)'] = combined_queue_df["Queue Time"].astype(float) / 60 

        fig_queue_2 = px.histogram(combined_queue_df,
                            x = "Arrival to hospital (days)",
                            y = "Queue Time (h)",
                            color = "Queue Type",
                            title = "Clinical Queue Times over Time"
                            )
        st.plotly_chart (fig_queue_2)
        # graph to demonstrate queue time for a bed (from disposition)

        #results_after_warm_up = results[(results["Start Time in Days"] >= 7) &
                                            #(results["Patient Disposition"] == "admitted")
        #]

        results['Time to AMU bed (h)'] = results['Time to AMU bed'].astype(float) / 60

        fig_queue_bed = px.scatter (results,
                                 x = "Start Time in Days",
                                 y = "Time to AMU bed (h)",
                                 color = "Run ID",
                                 title = "AMU Bed Waits",
                                 )
        st.plotly_chart (fig_queue_bed)

        # using alternative event log data source

        filtered_df_queue_bed = latest_file[latest_file['Event'].isin(['Arrival to hospital','Request AMU Bed', 'AMU Bed Granted'])][['Timestamp', 'Run ID', 'Event', 'Patient ID']]
        pivot_filtered_df_queue_bed = filtered_df_queue_bed.pivot(index=['Patient ID','Run ID'], columns='Event', values='Timestamp').reset_index()
         # Then calculate queue time 
        pivot_filtered_df_queue_bed['Queue Time'] = pivot_filtered_df_queue_bed['AMU Bed Granted'].astype(float) - pivot_filtered_df_queue_bed['Arrival to hospital'].astype(float)
        pivot_filtered_df_queue_bed['Queue Type'] = 'AMU Bed'
        pivot_filtered_df_queue_bed = pivot_filtered_df_queue_bed.sort_values(by= ['Arrival to hospital'])

        pivot_filtered_df_queue_bed['Arrival to hospital (days)'] = pivot_filtered_df_queue_bed['Arrival to hospital'].astype(float) / 1440
        pivot_filtered_df_queue_bed['Queue Time (h)'] = pivot_filtered_df_queue_bed['Queue Time'].astype(float) / 60

        fig_queue_bed_2 = px.scatter (pivot_filtered_df_queue_bed,
                                 x = "Arrival to hospital (days)",
                                 y = "Queue Time (h)",
                                 color = "Run ID",
                                 title = "Time to AMU Bed from Admission",
                                 )
        fig_queue_bed_2.add_hline(y=median_value, 
              line_dash="dash", 
              line_color="yellow", 
              annotation_text=f"Median: {median_value:.2f}",
              annotation_position="top left")
        
        st.plotly_chart (fig_queue_bed_2)

        # graph to show patient location over time (SDEC, ED, AMU)

        sankey_df = latest_file

        #sankey_df['Timestamp'] = pd.to_datetime(sankey_df['Timestamp'])

        # create a list of transitions
        event_pairs = {
            'Arrival to hospital': 'Request Nurse',
            'Request Nurse': 'Nurse Start',
            'Nurse Start': 'Nurse Complete',
            'Request Doctor': 'Doctor Start',
            'Doctor Start': 'Doctor Complete',
            'Ix Started': 'Ix Complete',
            'Request Consultant': 'See Consultant',
            'See Consultant': 'Consultant Complete',
            'Request AMU Bed': 'AMU Bed Granted'
        }
        events_of_interest = list(event_pairs.keys())

        filtered_sankey_df = sankey_df[sankey_df["Event"].isin(events_of_interest)]

        # Pivot to wide format
        pivot_sankey_df = filtered_sankey_df.pivot_table(
            index=["Patient ID", "Run ID"],
            columns="Event",
            values="Timestamp",
            aggfunc="first"
        ).reset_index()

        transitions = []

        for _, row in pivot_sankey_df.iterrows():
            for from_event, to_event in event_pairs.items():
                if pd.notna(row.get(from_event)) and pd.notna(row.get(to_event)):
                    transitions.append((from_event, to_event))

        transition_df = pd.DataFrame(transitions, columns=["From", "To"])
        transition_counts = transition_df.value_counts().reset_index(name="Count")

        # Get unique labels and map them to indices
        labels = list(set(transition_counts["From"]).union(set(transition_counts["To"])))
        label_indices = {label: i for i, label in enumerate(labels)}

        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels
            ),
            link=dict(
                source=[label_indices[f] for f in transition_counts["From"]],
                target=[label_indices[t] for t in transition_counts["To"]],
                value=transition_counts["Count"]
            )
        )])

        #st.plotly_chart(fig_sankey)

    else:
        st.write("Awaiting results...")
        
# fourth tab for metrics and dials

# fifth tab for results table 
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

