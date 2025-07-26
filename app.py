import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime

# === Authenticate using Streamlit secrets ===
service_account_info = st.secrets["gcp_service_account"]
scoped_creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
client = gspread.authorize(scoped_creds)

# === Set Google Sheet Details ===
SHEET_NAME = "Construction Inventory"  # Or use URL: st.secrets["sheet_url"]

# === Function to connect to specific worksheet ===
def connect_to_gsheet(sheet_name, worksheet_name):
    worksheet = client.open(sheet_name).worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# === Material and Unit Options for Dropdowns ===
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

# === Inward Register Tab ===
with tabs[1]:
    st.header("📦 Inward Register")

    WORKSHEET_NAME = "Inward Register"

    try:
        inward_df = connect_to_gsheet(SHEET_NAME, WORKSHEET_NAME)
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        inward_df = pd.DataFrame(columns=[
            "Date", "Material", "Vendor Name", "Quantity", "Unit", "Rate per Unit",
            "Amount", "Invoice Number", "Received By", "Remarks", "Expiry Date"
        ])

    with st.form("inward_form"):
        st.subheader("➕ Add Inward Entry")

        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date", datetime.now().date())
            material = st.selectbox("Material", material_options)
            vendor_name = st.selectbox("Vendor Name", df["Vendor Name"].unique() if not df.empty else [])
            quantity = st.number_input("Quantity", min_value=0.0, format="%.2f")
            unit = st.selectbox("Unit", unit_options)
            rate = st.number_input("Rate per Unit", min_value=0.0, format="%.2f")

        with col2:
            invoice_number = st.text_input("Invoice Number")
            received_by = st.text_input("Received By")
            remarks = st.text_area("Remarks")
            expiry_date = st.date_input("Expiry Date", min_value=datetime.now().date())

        submitted = st.form_submit_button("Save Inward Entry")

        if submitted:
            amount = quantity * rate
            new_entry = {
                "Date": date.strftime("%Y-%m-%d"),
                "Material": material,
                "Vendor Name": vendor_name,
                "Quantity": quantity,
                "Unit": unit,
                "Rate per Unit": rate,
                "Amount": amount,
                "Invoice Number": invoice_number,
                "Received By": received_by,
                "Remarks": remarks,
                "Expiry Date": expiry_date.strftime("%Y-%m-%d")
            }

            inward_df = pd.concat([inward_df, pd.DataFrame([new_entry])], ignore_index=True)

            try:
                worksheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
                worksheet.clear()
                worksheet.update([inward_df.columns.values.tolist()] + inward_df.values.tolist())
                st.success("Inward entry added successfully.")
            except Exception as e:
                st.error(f"Failed to write to Google Sheet: {e}")

    st.subheader("📋 Inward Register Entries")
    st.dataframe(inward_df)

    st.download_button("⬇️ Download Inward Register", data=inward_df.to_csv(index=False), file_name="inward_register.csv", mime="text/csv")

# === Outward Register ===
with tabs[2]:
    st.header("📤 Outward Register")

    try:
        worksheet = client.open(SHEET_NAME).worksheet("Outward Register")
        outward_df = pd.DataFrame(worksheet.get_all_records())
    except Exception as e:
        st.error(f"Error loading Outward Register: {e}")
        outward_df = pd.DataFrame(columns=[
            "Date", "Material Name", "Quantity Issued", "Unit", "Issued To",
            "Purpose", "Authorized By", "Remarks", "Photographic Record"
        ])

    with st.form("outward_form"):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date", value=datetime.today())
            material_name = st.selectbox("Material Name", [
                "Cement", "Steel", "Sand", "Bricks", "Tiles", "Paint", "Other"])
            quantity = st.number_input("Quantity Issued", min_value=0.0)
            unit = st.selectbox("Unit", [
                "Bags", "Tons", "Liters", "Numbers", "Cubic Feet", "Cubic Meters"])
            issued_to = st.text_input("Issued To")

        with col2:
            purpose = st.text_input("Purpose of Issue")
            authorized_by = st.text_input("Authorized By")
            remarks = st.text_area("Remarks")
            photo = st.file_uploader("Upload Photo (Optional)", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("Submit")

        if submitted:
            photo_path = ""
            if photo:
                photo_path = os.path.join("data", photo.name)
                os.makedirs("data", exist_ok=True)
                with open(photo_path, "wb") as f:
                    f.write(photo.read())

            new_entry = {
                "Date": date.strftime("%Y-%m-%d"),
                "Material Name": material_name,
                "Quantity Issued": quantity,
                "Unit": unit,
                "Issued To": issued_to,
                "Purpose": purpose,
                "Authorized By": authorized_by,
                "Remarks": remarks,
                "Photographic Record": photo_path
            }

            try:
                worksheet.append_row(list(new_entry.values()))
                st.success("✅ Outward entry recorded!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Failed to record entry: {e}")

    st.subheader("📄 Outward Register Entries")
    if not outward_df.empty:
        st.dataframe(outward_df)
        st.download_button("⬇️ Download Outward Register", outward_df.to_csv(index=False), "outward_register.csv", "text/csv")
    else:
        st.info("No outward entries found.")





























