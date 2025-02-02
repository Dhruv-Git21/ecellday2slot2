import streamlit as st
import pandas as pd
import random
from datetime import datetime

# Load datasets
mentors = pd.read_csv("Mentors Slot 2 Day 2 - Sheet2.csv")  # Columns: Name, Sector 1, Sector 2, Sector 3, Index
startups = pd.read_csv("Startup Slot 2 Day 2 - Sheet1.csv")  # Columns: Name, Sector, Index, Contacts

# Fill empty preferences with "Agnostic"
mentors.fillna("Agnostic", inplace=True)

# Function to allocate a startup to a mentor
def allocate_startup(mentor_name, startup_name=None):
    if startup_name:
        # Manual selection
        selected_startup = st.session_state.startups[st.session_state.startups["Name"] == startup_name]
        if selected_startup.empty or startup_name in st.session_state.mentors_assigned[mentor_name]:
            st.warning("Invalid selection or startup already assigned to this mentor.")
            return
        selected_startup = selected_startup.iloc[0]
    else:
        # Auto selection based on mentor preference
        preferences = st.session_state.mentor_preferences[mentor_name]
        
        if "Agnostic" in preferences:
            available_startups = st.session_state.startups[
                (~st.session_state.startups["Name"].isin(st.session_state.mentors_assigned[mentor_name]))
            ]
        else:
            available_startups = st.session_state.startups[
                ((st.session_state.startups["Sector"].isin(preferences)) | (st.session_state.startups["Sector"] == "Other")) &
                (~st.session_state.startups["Name"].isin(st.session_state.mentors_assigned[mentor_name]))
            ]

        if available_startups.empty:
            st.warning(f"No available startups for {mentor_name}.")
            return

        selected_startup = available_startups.sample(1).iloc[0]

    # Record allocation time
    allocation_time = datetime.now().strftime("%I:%M %p")

    # Store the session
    st.session_state.mentor_sessions[mentor_name] = {
        "Startup": selected_startup["Name"],
        "Sector": selected_startup["Sector"],
        "Contacts": selected_startup["Contacts"],
        "Time": allocation_time,
    }

    # Mark startup as assigned
    st.session_state.mentors_assigned[mentor_name].add(selected_startup["Name"])
    st.session_state.startups_assigned.add(selected_startup["Name"])

# Initialize session state
if "mentor_sessions" not in st.session_state:
    st.session_state.mentor_sessions = {}

if "mentors_assigned" not in st.session_state:
    st.session_state.mentors_assigned = {mentor: set() for mentor in mentors["Name"].tolist()}

if "mentor_preferences" not in st.session_state:
    st.session_state.mentor_preferences = {
        mentor["Name"]: [mentor["Sector 1"], mentor["Sector 2"], mentor["Sector 3"]]
        if mentor["Sector 1"] != "Agnostic" else ["Agnostic"]
        for _, mentor in mentors.iterrows()
    }

if "startups" not in st.session_state:
    st.session_state.startups = startups

if "mentor_status" not in st.session_state:
    st.session_state.mentor_status = {mentor: "Create New Session" for mentor in mentors["Name"].tolist()}

if "startups_assigned" not in st.session_state:
    st.session_state.startups_assigned = set()

# Streamlit UI
st.title("Mentoring Session Scheduler")

# Manual Allocation Section
st.subheader("Manually Allocate a Mentor and Startup")

# Display mentor preferences next to their name
mentor_options = [
    f"{row['Name']} (Pref: {row['Sector 1']}, {row['Sector 2']}, {row['Sector 3']})"
    for _, row in mentors.iterrows()
]
mentor_selection = st.selectbox("Select Mentor", mentor_options)

# Extract the actual mentor name from the selection
mentor_name_selected = mentor_selection.split(" (")[0]

# Show startup sector alongside name
startup_options = [
    f"{row['Name']} (Sector: {row['Sector']})" for _, row in startups.iterrows()
]
startup_selection = st.selectbox("Select Startup", startup_options)

# Extract the actual startup name
startup_name_selected = startup_selection.split(" (")[0]

if st.button("Allocate Manually"):
    allocate_startup(mentor_name_selected, startup_name_selected)
    st.session_state.mentor_status[mentor_name_selected] = "End Session"
    st.rerun()

# Auto Allocation for Agnostic Mentors
if st.button("Generate Assignments"):
    for mentor_name in mentors["Name"]:
        if mentor_name not in st.session_state.mentor_sessions:
            allocate_startup(mentor_name)

    st.success("All mentors have been assigned startups!")
    st.rerun()

# Display mentor session controls
for _, mentor in mentors.iterrows():
    mentor_name = mentor["Name"]
    preferences_display = f"{mentor['Sector 1']}, {mentor['Sector 2']}, {mentor['Sector 3']}"

    st.subheader(f"Mentor: {mentor_name} (Pref: {preferences_display})")

    if mentor_name in st.session_state.mentor_sessions:
        session = st.session_state.mentor_sessions[mentor_name]
        st.write(f"**Startup:** {session['Startup']} | **Sector:** {session['Sector']} | **Contacts:** {session['Contacts']} | **Time:** {session['Time']}")

    # Toggle button for session creation & ending
    if st.button(st.session_state.mentor_status[mentor_name], key=mentor_name):
        if st.session_state.mentor_status[mentor_name] == "Create New Session":
            allocate_startup(mentor_name)
            st.session_state.mentor_status[mentor_name] = "End Session"
        else:
            del st.session_state.mentor_sessions[mentor_name]
            st.session_state.mentor_status[mentor_name] = "Create New Session"
        st.rerun()
