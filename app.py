import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
import os
from datetime import datetime

# === Authenticate using Streamlit secrets ===
service_account_info = st.secrets["gcp_service_account"]
scoped_creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)
client = gspread.authorize(scoped_creds)

client = gspread.authorize(creds)

# === Set Google Sheet Details ===
SHEET_NAME = "Construction Inventory"

# === Function to connect to specific worksheet ===
def connect_to_gsheet(sheet_name, worksheet_name):
    worksheet = client.open(sheet_name).worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# === Material Options for Dropdowns ===
material_options = ["Cement", "Sand", "Steel", "Tiles", "Paint", "Bricks", "Aggregate", "Plywood"]
unit_options = ["Bags", "Tons", "Liters", "Numbers", "Cubic Feet", "Cubic Meters", "Kilograms", "Meters"]

# === Create Tabs ===
tabs = st.tabs([
    "Vendor Management",
    "Inward Register",
    "Outward Register",
    "Returns Register",
    "Damage / Loss",
    "Reconciliation",
    "Daily Closing",
    "Stock Summary",
    "BOQ Mapping",
    "Indent Register",
    "Material Transfer Register",
    "Scrap Register",
    "Rate Contract Register",
    "PO Register",
    "Reports Dashboard"
])

# === Vendor Management Tab ===
with tabs[0]:
    st.header("📋 Vendor Management")

    WORKSHEET_NAME = "Vendor Master"

    try:
        df = connect_to_gsheet(SHEET_NAME, WORKSHEET_NAME)
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        df = pd.DataFrame(columns=[
            "Vendor Name", "Contact Person", "Contact Number", "Email ID",
            "Address", "GST Number", "Bank Details", "Approved Materials",
            "Rate Agreement", "Payment Terms", "Performance Rating",
            "Status", "Remarks", "Document URL"
        ])

    # === Add / Update Vendor Form ===
    with st.form("add_vendor_form"):
        st.subheader("➕ Add / Update Vendor")

        col1, col2 = st.columns(2)

        with col1:
            vendor_name = st.text_input("Vendor Name")
            contact_person = st.text_input("Contact Person")
            contact_number = st.text_input("Contact Number")
            email = st.text_input("Email ID")
            address = st.text_area("Address")
            gst = st.text_input("GST Number / Tax ID")
            bank_details = st.text_area("Bank Details")

        with col2:
            approved_materials = st.multiselect("Approved Materials", material_options)
            rate_agreement = st.text_area("Rate Agreement")
            payment_terms = st.text_input("Payment Terms")
            rating = st.slider("Performance Rating", 0, 5, 3)
            status = st.selectbox("Status", ["Active", "Inactive"])
            remarks = st.text_area("Remarks")
            uploaded_file = st.file_uploader("Upload Document (optional)", type=["pdf", "jpg", "png", "docx"])

        submitted = st.form_submit_button("Save Vendor")

        if submitted:
            os.makedirs("data", exist_ok=True)
            doc_url = ""
            if uploaded_file:
                save_path = os.path.join("data", uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.read())
                doc_url = save_path

            new_row = {
                "Vendor Name": vendor_name,
                "Contact Person": contact_person,
                "Contact Number": contact_number,
                "Email ID": email,
                "Address": address,
                "GST Number": gst,
                "Bank Details": bank_details,
                "Approved Materials": ', '.join(approved_materials),
                "Rate Agreement": rate_agreement,
                "Payment Terms": payment_terms,
                "Performance Rating": rating,
                "Status": status,
                "Remarks": remarks,
                "Document URL": doc_url
            }

            if vendor_name in df['Vendor Name'].values:
                df.loc[df['Vendor Name'] == vendor_name] = new_row
                st.success(f"Vendor '{vendor_name}' updated.")
            else:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Vendor '{vendor_name}' added.")

            try:
                worksheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
                worksheet.clear()
                worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            except Exception as e:
                st.error(f"Failed to write to Google Sheet: {e}")

    # === Vendor Master Table ===
    st.subheader("📌 Vendor Master List")
    st.dataframe(df)

    # === Export CSV ===
    st.download_button("⬇️ Download Vendor Master", data=df.to_csv(index=False), file_name="vendors.csv", mime="text/csv")



























