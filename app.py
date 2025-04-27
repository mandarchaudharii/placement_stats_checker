import streamlit as st
import pandas as pd
import re

# Load all tables
@st.cache_data
def load_data():
    xls = pd.ExcelFile("company_criteria.xlsx")
    data = {
        "2022": xls.parse("Table 1", skiprows=1),
        "2023": xls.parse("Table 2", skiprows=1),
        "2024": xls.parse("Table 3", skiprows=1),
    }
    for year in data:
        df = data[year]
        df.columns = ["Sl.No", "Offer", "Type", "Company", "Criteria", "Branches", "Profile"]
        data[year] = df.dropna(subset=["Company"])
    return data

data = load_data()

# Sidebar filters
st.sidebar.title("Student Info")
year = st.sidebar.selectbox("Select Batch Year", ["2022", "2023", "2024"])
cgpa = st.sidebar.number_input("Enter CGPA", min_value=0.0, max_value=10.0, step=0.1)
backlogs = st.sidebar.number_input("No. of Active Backlogs", min_value=0, step=1)
perc_10 = st.sidebar.number_input("10th %", min_value=0.0, max_value=100.0, step=0.1)
perc_12 = st.sidebar.number_input("12th %", min_value=0.0, max_value=100.0, step=0.1)
branch = st.sidebar.text_input("Your Branch (e.g., CS, IT, EC)")

st.title("Company Eligibility Filter")

# Parse requirement logic
def is_eligible(row):
    crit = str(row["Criteria"]).lower()
    branches = str(row["Branches"]).lower()

    try:
        cgpa_req = float(re.search(r'(\d+(\.\d+)?)\s*cgpa', crit).group(1))
    except:
        cgpa_req = 0

    try:
        bl_req = int(re.search(r'(\d+)\s*bl', crit).group(1))
    except:
        bl_req = 0 if "no bl" in crit else 99

    perc_10_req = 0
    perc_12_req = 0

    # Find all percentages with what they apply to
    for perc_match in re.finditer(r'(\d+(\.\d+)?)%\s*\((.*?)\)', crit):
        perc_value = float(perc_match.group(1))
        categories = perc_match.group(3)

        if "10" in categories:
            perc_10_req = max(perc_10_req, perc_value)
        if "12" in categories or "diploma" in categories:
            perc_12_req = max(perc_12_req, perc_value)

    return (
        cgpa >= cgpa_req and
        backlogs <= bl_req and
        perc_10 >= perc_10_req and
        perc_12 >= perc_12_req and
        branch.lower() in branches
    )

# Filter and display
if st.sidebar.button("Search Companies"):
    df = data[year]
    filtered = df[df.apply(is_eligible, axis=1)][["Company", "Offer", "Criteria", "Branches", "Profile"]]

    if not filtered.empty:
        st.success(f"Found {len(filtered)} eligible companies.")

        # New Filter after results
        offer_type = st.selectbox("Select Offer Type", ["All", "P", "I", "P+I"])
        if offer_type != "All":
            filtered = filtered[filtered["Offer"].str.strip().str.upper() == offer_type.upper()]

        st.dataframe(filtered.reset_index(drop=True))

    else:
        st.warning("No matching companies found.")
