import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from datetime import datetime
import plotly.graph_objects as go

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("medical_data.db")
    cursor = conn.cursor()

    # Create tables for medical data, notifications, and medications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            blood_pressure TEXT NOT NULL,
            heart_rate INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            abnormal_data TEXT NOT NULL,
            abnormal_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            medication_name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    return conn, cursor

# Validate blood pressure input format
def validate_bp(bp):
    parts = bp.split('/')
    if len(parts) != 2:
        return False
    systolic, diastolic = parts
    if not (systolic.isdigit() and diastolic.isdigit()):
        return False
    systolic = int(systolic)
    diastolic = int(diastolic)
    return 50 <= systolic <= 250 and 30 <= diastolic <= 150

# Function to validate input fields
def validate_inputs(name, age, bp, hr):
    if not name:
        st.error("Patient name is required.")
        return False
    if not age.isdigit() or not (1 <= int(age) <= 120):
        st.error("Please enter a valid age (1-120).")
        return False
    if not validate_bp(bp):
        st.error("Please enter blood pressure in format systolic/diastolic (e.g., 120/80).")
        return False
    if not hr.isdigit() or not (30 <= int(hr) <= 200):
        st.error("Please enter a valid heart rate (30-200 bpm).")
        return False
    return True

# Submit data to the database
def submit_data(name, age, bp, hr, conn, cursor):
    cursor.execute("""
        INSERT INTO medical_data (name, age, blood_pressure, heart_rate)
        VALUES (?, ?, ?, ?)
    """, (name, int(age), bp, int(hr)))
    conn.commit()

    # Check for abnormalities
    abnormality = detect_abnormal_data(name, bp, hr)
    if abnormality:
        cursor.execute("""
            INSERT INTO notifications (name, abnormal_data, abnormal_type)
            VALUES (?, ?, ?)
        """, (name, abnormality['data'], abnormality['type']))
        conn.commit()
        st.success(f"Notification created for abnormal {abnormality['type']}!")

    st.success("Data submitted successfully!")

# Detect abnormal data points
def detect_abnormal_data(name, bp, hr):
    systolic, diastolic = map(int, bp.split('/'))
    hr = int(hr)

    if hr < 60 or hr > 100:
        return {"data": f"Heart Rate: {hr} bpm", "type": "Heart Rate"}

    if systolic > 140 or diastolic > 90:
        return {"data": f"Blood Pressure: {systolic}/{diastolic} mmHg", "type": "Blood Pressure"}

    return None

# View submitted data as a dataframe
def view_data(cursor):
    cursor.execute("SELECT * FROM medical_data")
    records = cursor.fetchall()
    if records:
        df = pd.DataFrame(records, columns=["ID", "Name", "Age", "Blood Pressure", "Heart Rate", "Timestamp"])
        st.dataframe(df)
        return df
    else:
        st.warning("No data found.")
        return pd.DataFrame()

# Log medication to the database
def log_medication(name, med_name, dosage, conn, cursor):
    cursor.execute("""
        INSERT INTO medications (patient_name, medication_name, dosage)
        VALUES (?, ?, ?)
    """, (name, med_name, dosage))
    conn.commit()

# View medications as a dataframe
def view_medications(cursor):
    cursor.execute("SELECT * FROM medications")
    records = cursor.fetchall()
    if records:
        df = pd.DataFrame(records, columns=["ID", "Patient Name", "Medication Name", "Dosage", "Timestamp"])
        st.dataframe(df)
        return df
    else:
        st.warning("No medications logged.")
        return pd.DataFrame()

# Plot heart rate and blood pressure
# Plot heart rate and blood pressure, highlighting abnormal values
def plot_data(df):
    if not df.empty:
        # Identify abnormal heart rates
        df['Heart Rate Abnormal'] = df['Heart Rate'].apply(lambda x: x < 60 or x > 100)
        df['Systolic'] = df['Blood Pressure'].apply(lambda x: int(x.split('/')[0]))
        df['Diastolic'] = df['Blood Pressure'].apply(lambda x: int(x.split('/')[1]))
       
        # Identify abnormal blood pressure values
        df['Blood Pressure Abnormal'] = df.apply(lambda row: row['Systolic'] > 140 or row['Diastolic'] > 90, axis=1)
 
        # Plot heart rate with abnormal points highlighted
        fig1 = px.scatter(df, x='Timestamp', y='Heart Rate', color='Heart Rate Abnormal',
                  color_discrete_map={True: 'red', False: 'blue'},
                  title='Heart Rate Over Time', labels={'Heart Rate Abnormal': 'Abnormal Heart Rate'})
 
        # Add a line connecting all data points
        fig1.add_trace(go.Scatter(x=df['Timestamp'], y=df['Heart Rate'],
                                mode='lines', line=dict(color='gray'), name='Line Through Points'))
 
        st.plotly_chart(fig1)
 
        # Scatter plot for Systolic and Diastolic with colors based on 'Blood Pressure Abnormal'
        fig2 = px.scatter(df, x='Timestamp', y=['Systolic', 'Diastolic'], color='Blood Pressure Abnormal',
                        color_discrete_map={True: 'red', False: 'blue'},
                        title='Blood Pressure (Systolic/Diastolic) Over Time',
                        labels={'Blood Pressure Abnormal': 'Abnormal Blood Pressure'})
 
        # Add a line for Systolic points
        fig2.add_trace(go.Scatter(x=df['Timestamp'], y=df['Systolic'],
                                mode='lines', line=dict(color='gray'), name='Systolic Line'))
 
        # Add a line for Diastolic points
        fig2.add_trace(go.Scatter(x=df['Timestamp'], y=df['Diastolic'],
                                mode='lines', line=dict(color='darkgray'), name='Diastolic Line'))
 
        st.plotly_chart(fig2)

# Notifications Page
def notifications_page(cursor):
    st.write("### Notifications")

    # Fetch notifications from the database
    cursor.execute("SELECT * FROM notifications ORDER BY timestamp DESC")
    notifications = cursor.fetchall()

    if notifications:
        for notif in notifications:
            st.write(f"**{notif[3]}** - **{notif[1]}** ({notif[2]})")
    else:
        st.info("No notifications available.")

    # Simulate a map with the user's current location and the nearest hospital
    st.write("### Nearby Hospital Route")
    
    # Example location (lat, lon) - Simulating user location
    user_location = [35.7796, -78.6382]  # Raleigh, NC (dummy)
    nearest_hospital = [35.7801, -78.6392]  # Dummy hospital location
    
    # Create map with user location and hospital
    map_ = folium.Map(location=user_location, zoom_start=14)
    
    # Add markers for user location and hospital
    folium.Marker(user_location, tooltip="Your Location", icon=folium.Icon(color="blue")).add_to(map_)
    folium.Marker(nearest_hospital, tooltip="Nearest Hospital", icon=folium.Icon(color="red")).add_to(map_)
    
    # Draw route (simulated)
    folium.PolyLine(locations=[user_location, nearest_hospital], color="green", weight=2.5).add_to(map_)
    
    # Display map in Streamlit
    st_folium(map_, width=700, height=500)

# Main Streamlit app logic
def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.selectbox("Go to", ["Data Input", "Notifications", "Medication Tracker"])

    # Initialize the database
    conn, cursor = init_db()

    if selection == "Data Input":
        st.title("Senior Safe - Medical Data Input")

        # Use columns for neater input layout
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Patient Name")
            age = st.text_input("Age")

        with col2:
            bp = st.text_input("Blood Pressure (mmHg)", placeholder="e.g., 120/80")
            hr = st.text_input("Heart Rate (bpm)")

        # Submit button
        if st.button("Submit"):
            if validate_inputs(name, age, bp, hr):
                submit_data(name, age, bp, hr, conn, cursor)

        # Display submitted data
        st.write("### Submitted Medical Data")
        df = view_data(cursor)

        # Plot heart rate and blood pressure with abnormal data highlighted
        if not df.empty:
            st.write("### Visualizations")
            plot_data(df)

    elif selection == "Notifications":
        notifications_page(cursor)

    elif selection == "Medication Tracker":
        st.title("Medication Tracker")
        
        # Input form for medication logging
        name = st.text_input("Patient Name")
        med_name = st.text_input("Medication Name")
        dosage = st.text_input("Dosage")

        if st.button("Log Medication"):
            if name and med_name and dosage:
                log_medication(name, med_name, dosage, conn, cursor)
                st.success(f"{med_name} logged for {name} successfully!")
            else:
                st.error("Please fill in all fields.")

        # Display medication history
        st.write("### Medication History")
        df_med = view_medications(cursor)

if __name__ == "__main__":
    main()
