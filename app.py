"""State Life plan calculator - Streamlit app.

Rates are read from rate_list.xlsx (sheets: Rates, Plans).
Rate = premium per 1,000 sum assured for the given entry age.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

EXCEL_FILE = Path(__file__).parent / "rate_list.xlsx"

st.set_page_config(page_title="State Life Plan Calculator", page_icon="📊", layout="centered")


@st.cache_data
def load_data(path):
    rates = pd.read_excel(path, sheet_name="Rates")
    plans = pd.read_excel(path, sheet_name="Plans").set_index("Plan")
    return rates, plans


def pkr(x):
    return f"PKR {x:,.0f}"


rates, plans = load_data(EXCEL_FILE)
plan_names = plans.index.tolist()

st.title("State Life Plan Calculator")
st.caption("Approximate figures from the rate list. Actual policy values may differ.")

tab_calc, tab_rates = st.tabs(["Calculator", "Rate List"])

# ---------------- Calculator ----------------
with tab_calc:
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input(
            "Age",
            min_value=int(rates["Age"].min()),
            max_value=int(rates["Age"].max()),
            value=30,
            step=1,
        )
    with col2:
        plan = st.selectbox("Plan", plan_names)

    info = plans.loc[plan]
    pay_years = int(info["Payment Years"])
    maturity_years = int(info["Maturity Years"])
    multiple = float(info["Approx Return Multiple"])

    plan_rates = rates[["Age", plan]].dropna()
    row = plan_rates[plan_rates["Age"] == age]

    if row.empty:
        st.error(
            f"{plan} is available for ages {int(plan_rates['Age'].min())} "
            f"to {int(plan_rates['Age'].max())} only."
        )
        st.stop()

    rate = float(row[plan].iloc[0])
    per_lakh = rate * 100  # premium for 100,000 sum assured

    st.info(
        f"**{plan}**: pay for {pay_years} years, matures after {maturity_years} years, "
        f"approx {multiple:g}x return. Rate at age {age}: **{rate:.2f}**"
    )

    mode = st.radio(
        "What do you want to enter?",
        ["Annual payment", "Sum assured"],
        horizontal=True,
    )

    if mode == "Annual payment":
        premium = st.number_input(
            "Annual payment (PKR)", min_value=1000, value=100000, step=5000
        )
        sum_assured = premium / per_lakh * 100000
    else:
        sum_assured = st.number_input(
            "Sum assured (PKR)", min_value=10000, value=1000000, step=50000
        )
        premium = sum_assured / 100000 * per_lakh

    basis = st.radio(
        "Approx return calculated on",
        ["Sum assured", "Total amount paid"],
        horizontal=True,
    )

    total_paid = premium * pay_years
    base = sum_assured if basis == "Sum assured" else total_paid
    maturity_value = base * multiple

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Annual payment", pkr(premium))
    m2.metric("Sum assured", pkr(sum_assured))
    m3.metric("Approx maturity value", pkr(maturity_value))

    m4, m5, m6 = st.columns(3)
    m4.metric("Pay for", f"{pay_years} years")
    m5.metric("Total paid", pkr(total_paid))
    m6.metric("Matures at age", f"{age + maturity_years}")

    with st.expander("How it's calculated"):
        st.write(f"**Step 1.** {rate:.2f} × 100 = {per_lakh:,.0f}  (yearly payment for 100,000 sum assured)")
        if mode == "Annual payment":
            st.write(
                f"**Step 2.** {premium:,.0f} ÷ {per_lakh:,.0f} × 100,000 = "
                f"**{sum_assured:,.0f}** sum assured"
            )
        else:
            st.write(
                f"**Step 2.** {sum_assured:,.0f} ÷ 100,000 × {per_lakh:,.0f} = "
                f"**{premium:,.0f}** annual payment"
            )
        st.write(
            f"**Step 3.** {premium:,.0f} × {pay_years} years = {total_paid:,.0f} total paid"
        )
        st.write(
            f"**Step 4.** {base:,.0f} ({basis.lower()}) × {multiple:g} = "
            f"**{maturity_value:,.0f}** approx at maturity (after {maturity_years} years)"
        )

# ---------------- Rate list ----------------
with tab_rates:
    st.subheader("Plans")
    st.dataframe(plans, width="stretch")

    st.subheader("Rate list (per 1,000 sum assured)")
    st.dataframe(
        rates.style.format({p: "{:.2f}" for p in plan_names}, na_rep="—"),
        width="stretch",
        hide_index=True,
        height=600,
    )

    st.download_button(
        "Download rate list (Excel)",
        data=EXCEL_FILE.read_bytes(),
        file_name="rate_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
