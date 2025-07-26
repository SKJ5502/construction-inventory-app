import streamlit as st
import pandas as pd
import datetime
import math
from helpers.gsheet_utils import connect_sheet
import os
from datetime import datetime

import streamlit as st
import pandas as pd
import os

# Create data folder if not exists
os.makedirs("data", exist_ok=True)
DATA_PATH = "data/vendors.csv"

# === Tabs at the TOP ===
tabs = st.tabs([
    "Vendor Management",
    "Inward Register",
    "Outward Register"
])

# === Vendor Management Tab ===
with tabs[0]:
    st.header("📋 Vendor Management")

    # === Load or initialize data ===
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=[
            "Vendor Name", "Contact Person", "Contact Number", "Email ID",
            "Address", "GST Number", "Bank Details", "Approved Materials",
            "Rate Agreement", "Payment Terms", "Performance Rating",
            "Status", "Remarks", "Document URL"
        ])
        df.to_csv(DATA_PATH, index=False)
    else:
        df = pd.read_csv(DATA_PATH)

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
            master_materials = ["Cement", "Steel", "Sand", "Bricks", "Tiles"]
            approved_materials = st.multiselect("Approved Materials", master_materials)
            rate_agreement = st.text_area("Rate Agreement")
            payment_terms = st.text_input("Payment Terms")
            rating = st.slider("Performance Rating", 0, 5, 3)
            status = st.selectbox("Status", ["Active", "Inactive"])
            remarks = st.text_area("Remarks")
            uploaded_file = st.file_uploader("Upload Document (optional)", type=["pdf", "jpg", "png", "docx"])

        submitted = st.form_submit_button("Save Vendor")

        if submitted:
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

            df.to_csv(DATA_PATH, index=False)

    # === Vendor Master Table ===
    st.subheader("📌 Vendor Master List")
    st.dataframe(df)

    # === Export ===
    st.download_button("⬇️ Download Vendor Master", data=df.to_csv(index=False), file_name="vendors.csv", mime="text/csv")

# === Inward Register ===
with tabs[1]:
    st.header("📥 Inward Register")

    # Load existing inward data or create fresh file
    inward_data_path = "data/inward_register.csv"
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(inward_data_path):
        inward_df = pd.DataFrame(columns=[
            "Date & Time", "Vendor Name", "Invoice Number", "PO Number",
            "Material Name", "Unit", "Quantity Received", "Condition",
            "Expiry Date", "Vehicle Details", "Received By",
            "Quality Check Status", "Photographic Record", "Storage Location",
            "Remarks", "Authorized By"
        ])
        inward_df.to_csv(inward_data_path, index=False)
    else:
        inward_df = pd.read_csv(inward_data_path)

    with st.form("inward_form"):
        st.subheader("➕ Add Inward Entry")
        col1, col2 = st.columns(2)

        with col1:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.text_input("Date & Time of Receipt", value=current_time, disabled=True, key="timestamp")
            vendor_name = st.text_input("Vendor Name")
            invoice_number = st.text_input("Delivery Challan / Invoice Number")
            po_number = st.text_input("Purchase Order Number")
            material_options = ["Cement", "Sand", "Steel", "Tiles", "Paint"]
            material = st.selectbox("Material Name", material_options)
            unit_options = ["Bags", "Tons", "Liters", "Numbers", "Cubic Feet", "Cubic Meters"]
            unit = st.selectbox("Unit of Measurement (UOM)", unit_options)
            quantity = st.number_input("Quantity Received", min_value=0.0, format="%.2f")
            condition = st.text_input("Condition of Material")

        with col2:
            expiry_date = st.date_input("Expiry Date (optional)", value=None)
            vehicle_details = st.text_input("Vehicle Details (Truck No., Driver Name)")
            received_by = st.text_input("Received By")
            qc_status = st.text_input("Quality Check Status")
            photo = st.file_uploader("Photographic Record (Upload)", type=["jpg", "jpeg", "png", "pdf"])
            storage_location = st.text_input("Storage Location")
            remarks = st.text_area("Remarks / Notes")
            authorized_by = st.text_input("Authorization (Name / Signature)")

        submitted = st.form_submit_button("Save Inward Entry")

        if submitted:
            # Save photo file (if uploaded)
            photo_path = ""
            if photo:
                photo_path = os.path.join("data", photo.name)
                with open(photo_path, "wb") as f:
                    f.write(photo.read())

            new_inward = {
                "Date & Time": current_time,
                "Vendor Name": vendor_name,
                "Invoice Number": invoice_number,
                "PO Number": po_number,
                "Material Name": material,
                "Unit": unit,
                "Quantity Received": quantity,
                "Condition": condition,
                "Expiry Date": expiry_date if expiry_date else "",
                "Vehicle Details": vehicle_details,
                "Received By": received_by,
                "Quality Check Status": qc_status,
                "Photographic Record": photo_path,
                "Storage Location": storage_location,
                "Remarks": remarks,
                "Authorized By": authorized_by
            }

            inward_df = pd.concat([inward_df, pd.DataFrame([new_inward])], ignore_index=True)
            inward_df.to_csv(inward_data_path, index=False)
            st.success("Inward entry saved successfully!")

    # Display the existing data
    st.subheader("📄 Inward Register Entries")
    st.dataframe(inward_df)

    # Export button
    st.download_button("⬇️ Download Inward Register", inward_df.to_csv(index=False), "inward_register.csv", "text/csv")

# === Outward Register ===
with tabs[2]:
    st.header("📤 Outward Register")

    OUTWARD_CSV = "data/outward_register.csv"
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(OUTWARD_CSV):
        outward_df = pd.DataFrame(columns=[
            "Date", "Material Name", "Quantity Issued", "Unit", "Issued To",
            "Purpose", "Authorized By", "Remarks", "Photographic Record"
        ])
        outward_df.to_csv(OUTWARD_CSV, index=False)

    outward_df = pd.read_csv(OUTWARD_CSV)

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

            outward_df = pd.concat([outward_df, pd.DataFrame([new_entry])], ignore_index=True)
            outward_df.to_csv(OUTWARD_CSV, index=False)
            st.success("Outward entry recorded!")

    st.subheader("📄 Outward Register Entries")
    st.dataframe(outward_df)
    st.download_button("⬇️ Download Outward Register", outward_df.to_csv(index=False), "outward_register.csv", "text/csv")


