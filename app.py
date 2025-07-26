import streamlit as st
import pandas as pd
import datetime
import math
from helpers.gsheet_utils import connect_sheet
import os
from datetime import datetime

st.set_page_config(page_title="Construction Inventory", layout="wide")
sheet = connect_sheet("Construction Inventory")

st.title("🏗️ Construction Site Inventory Management System")

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
    "Material Transfer",
    "Scrap Register",
    "Rate Contract",
    "PO Register",
    "Reports Dashboard",
    "User Management"
])


# ✅ Make sure the folder exists
FOLDER_PATH = 'data'
if not os.path.exists(FOLDER_PATH):
    os.makedirs(FOLDER_PATH)

# ✅ Define the vendors.csv path BEFORE using it
DATA_PATH = os.path.join(FOLDER_PATH, 'vendors.csv')

    # === Vendor Management ===

    # Example for top-level tabs
    tabs = st.tabs(["Vendor Management"])  # Or include all your tabs here

    with tabs[0]:
        st.header("📋 Vendor Management")

    # === Load existing ===
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=[
            "Vendor Name", "Contact Person", "Contact Number", "Email ID",
            "Address", "GST Number", "Bank Details", "Approved Materials",
            "Rate Agreement", "Payment Terms", "Performance Rating",
            "Status", "Remarks", "Document URL"
        ])
        df.to_csv(DATA_PATH, index=False)

    df = pd.read_csv(DATA_PATH)

    # === Add New Vendor ===
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
            bank_details = st.text_area("Bank Details (optional)")

        with col2:
            master_materials = ["Cement", "Steel", "Sand", "Bricks", "Tiles"]
            approved_materials = st.multiselect(
                "Approved Materials", master_materials)
            rate_agreement = st.text_area("Rate Agreement (optional)")
            payment_terms = st.text_input("Payment Terms")
            rating = st.slider("Performance Rating", 0, 5, 3)
            status = st.selectbox("Status", ["Active", "Inactive"])
            remarks = st.text_area("Remarks")

            uploaded_file = st.file_uploader(
                "Upload Document (optional)", type=["pdf", "jpg", "png", "docx"])

        submitted = st.form_submit_button("Save Vendor")

        if submitted:
            doc_url = ""
            if uploaded_file:
                # Save file in data/ folder
                file_save_path = os.path.join(FOLDER_PATH, uploaded_file.name)
                with open(file_save_path, "wb") as f:
                    f.write(uploaded_file.read())
                doc_url = file_save_path

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

            # Check if vendor already exists — update or append
            if vendor_name in df['Vendor Name'].values:
                df.loc[df['Vendor Name'] == vendor_name] = new_row
                st.success(f"Vendor '{vendor_name}' updated!")
            else:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Vendor '{vendor_name}' added!")

            df.to_csv(DATA_PATH, index=False)

    # === Vendor Table ===
    st.subheader("📌 Vendor Master")
    st.dataframe(df)

    # === Export ===
    st.download_button(
        "⬇️ Download Vendor Master",
        df.to_csv(index=False),
        file_name="vendors.csv",
        mime="text/csv"
    )

     # === Paths ===
    FOLDER_PATH = 'data'
    if not os.path.exists(FOLDER_PATH):
        os.makedirs(FOLDER_PATH)

    vendor_file = os.path.join(FOLDER_PATH, 'vendors.csv')
    inward_file = os.path.join(FOLDER_PATH, 'inward.csv')

    # === Load Vendor Master ===
    if os.path.exists(vendor_file):
        vendor_df = pd.read_csv(vendor_file)
        approved_vendors = vendor_df[vendor_df['Status'] == 'Active']["Vendor Name"].unique().tolist()
    else:
        approved_vendors = []

    # === Prepare Inward File ===
    if not os.path.exists(inward_file):
        inward_df = pd.DataFrame(columns=[
            "Date & Time", "Supplier/Vendor Name", "Delivery Challan/Invoice Number",
            "Purchase Order Number", "Material Name", "Unit of Measurement",
            "Quantity Received", "Condition of Material", "Expiry Date",
            "Vehicle Details", "Received By", "Quality Check Status",
            "Photographic Record", "Storage Location", "Remarks/Notes", "Authorization"
        ])
        inward_df.to_csv(inward_file, index=False)
    else:
        inward_df = pd.read_csv(inward_file)

    # === Create Tabs ===
    tabs = st.tabs(["Vendor Management", "Inward Register"])

    # === Inward Register ===
    with tabs[1]:
        st.header("📥 Inward Register")

        st.subheader("➕ New Inward Entry")

        with st.form("inward_form"):
            col1, col2 = st.columns(2)

            with col1:
                date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                supplier = st.selectbox("Supplier/Vendor Name", approved_vendors)
                dc_number = st.text_input("Delivery Challan/Invoice Number")
                po_number = st.text_input("Purchase Order Number")
                material_name = st.selectbox(
                    "Material Name",
                    ["Cement", "Sand", "Steel", "Tiles", "Paint"]
                )
                unit = st.selectbox(
                    "Unit of Measurement",
                    ["Bags", "Tons", "Liters", "Numbers", "Cubic Feet", "Cubic Meters"]
                )
                quantity = st.number_input("Quantity Received", min_value=0.0, step=0.1)
                condition = st.text_input("Condition of Material")
                expiry_date = st.date_input("Expiry Date (optional)")

            with col2:
                vehicle_details = st.text_input("Vehicle Details (Truck Number & Driver Name)")
                received_by = st.text_input("Received By")
                qc_status = st.text_input("Quality Check Status")
                photo = st.file_uploader("Photographic Record", type=["jpg", "png", "jpeg"])
                storage_location = st.text_input("Storage Location")
                remarks = st.text_area("Remarks / Notes")
                authorization = st.text_input("Authorization (Name)")

            # ✅ THIS must be INSIDE the form
            submit = st.form_submit_button("Save Inward Entry")

            # ✅ This is outside the form
    if submit:
        photo_url = ""
        if photo:
            photo_save_path = os.path.join(FOLDER_PATH, f"inward_{photo.name}")
            with open(photo_save_path, "wb") as f:
                f.write(photo.read())
            photo_url = photo_save_path

        new_inward = {
            "Date & Time": date_time,
            "Supplier/Vendor Name": supplier,
            "Delivery Challan/Invoice Number": dc_number,
            "Purchase Order Number": po_number,
            "Material Name": material_name,
            "Unit of Measurement": unit,
            "Quantity Received": quantity,
            "Condition of Material": condition,
            "Expiry Date": expiry_date,
            "Vehicle Details": vehicle_details,
            "Received By": received_by,
            "Quality Check Status": qc_status,
            "Photographic Record": photo_url,
            "Storage Location": storage_location,
            "Remarks/Notes": remarks,
            "Authorization": authorization
        }

        inward_df = pd.concat([inward_df, pd.DataFrame([new_inward])], ignore_index=True)
        inward_df.to_csv(inward_file, index=False)
        st.success("Inward entry saved successfully!")


        st.subheader("📑 Inward Register Data")
        st.dataframe(inward_df)

        st.download_button(
            "⬇️ Download Inward Register",
            inward_df.to_csv(index=False),
            file_name="inward_register.csv",
            mime="text/csv"
        )

