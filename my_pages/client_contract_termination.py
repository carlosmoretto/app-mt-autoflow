import streamlit as st
import pandas as pd
from datetime import date

def show():
    st.title("Termination Calculation")
    st.write("This page helps to calculate termination settlements.")

    # Example form for termination calculation input
    with st.form("termination_calculation_form"):
        employee_name = st.text_input("Employee Name")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date", value=date.today())
        salary = st.number_input("Monthly Salary", min_value=0.0, step=0.01)
        calculate_button = st.form_submit_button(label="Calculate Termination Settlement")

    if calculate_button:
        # Calculate duration of employment
        duration = (end_date - start_date).days
        # Simple example calculation for settlement amount
        settlement_amount = (salary / 30) * duration
        
        st.write(f"Employee: {employee_name}")
        st.write(f"Start Date: {start_date}")
        st.write(f"End Date: {end_date}")
        st.write(f"Duration of Employment: {duration} days")
        st.write(f"Settlement Amount: ${settlement_amount:,.2f}")
        
        # Example DataFrame for display
        data = {
            "Employee Name": [employee_name],
            "Start Date": [start_date],
            "End Date": [end_date],
            "Duration (days)": [duration],
            "Settlement Amount": [settlement_amount]
        }
        df = pd.DataFrame(data)
        st.dataframe(df)
