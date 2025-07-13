import streamlit as st
import math

st.set_page_config(page_title="Quick Financial Calculator", layout="centered")
st.title("Quick Financial Calculator")

calc_type = st.selectbox("Choose a Calculator:", [
    "Compound Interest",
    "Retirement Savings",
    "Loan Repayment"
])

st.markdown("---")

if calc_type == "Compound Interest":
    st.header("Compound Interest Calculator")
    principal = st.number_input("Initial Investment ($)", value=1000.0)
    rate = st.number_input("Annual Interest Rate (%)", value=5.0)
    years = st.number_input("Years", value=10)
    frequency = st.selectbox("Compounding Frequency", ["Annually", "Semiannually", "Quarterly", "Monthly"])

    freq_map = {"Annually": 1, "Semiannually": 2, "Quarterly": 4, "Monthly": 12}
    n = freq_map[frequency]
    future_value = principal * (1 + rate / 100 / n) ** (n * years)

    st.success(f"Future Value: ${future_value:,.2f}")

elif calc_type == "Retirement Savings":
    st.header("Retirement Savings Estimator")
    current_age = st.number_input("Current Age", value=30)
    retirement_age = st.number_input("Retirement Age", value=65)
    monthly_contrib = st.number_input("Monthly Contribution ($)", value=500.0)
    annual_return = st.number_input("Expected Annual Return (%)", value=6.0)

    months = (retirement_age - current_age) * 12
    monthly_rate = annual_return / 100 / 12
    future_value = monthly_contrib * (((1 + monthly_rate) ** months - 1) / monthly_rate)

    st.success(f"Estimated Savings at Retirement: ${future_value:,.2f}")

elif calc_type == "Loan Repayment":
    st.header("Loan Repayment Calculator")
    loan_amount = st.number_input("Loan Amount ($)", value=25000.0)
    annual_rate = st.number_input("Annual Interest Rate (%)", value=4.5)
    years = st.number_input("Loan Term (Years)", value=5)

    monthly_rate = annual_rate / 100 / 12
    payments = years * 12
    if monthly_rate > 0:
        monthly_payment = loan_amount * monthly_rate / (1 - (1 + monthly_rate) ** -payments)
    else:
        monthly_payment = loan_amount / payments

    st.success(f"Monthly Payment: ${monthly_payment:,.2f}")
    st.info(f"Total Payment: ${monthly_payment * payments:,.2f}")
