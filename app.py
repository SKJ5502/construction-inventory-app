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

st.set_page_config(page_title="Construction Site Inventory", layout="wide")

# === Create data folder if not exists ===
if not os.path.exists("data"):
    os.makedirs("data")

# === Load Vendor Data ===
vendor_file = "data/vendor.csv"
if os.path.exists(vendor_file):
    vendor_df = pd.read_csv(vendor_file)
else:
    vendor_df = pd.DataFrame(columns=["Vendor ID", "Vendor Name", "Contact Person", "Phone", "Email", "Address", "GST Number"])

# === Dropdown Options ===
material_options = ["Cement", "Sand", "Steel", "Tiles", "Paint", "Bricks", "Aggregate", "Plywood"]
unit_options = ["Bags", "Tons", "Liters", "Numbers", "Cubic Feet", "Cubic Meters", "Kilograms", "Meters"]

# === Tabs at the TOP ===
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
    "Rate Contract Register"
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

# === Returns Register ===
with tabs[3]:
    st.header("🔁 Returns Register")

    RETURNS_CSV = "data/returns_register.csv"
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(RETURNS_CSV):
        returns_df = pd.DataFrame(columns=[
            "Date", "Material Name", "Quantity Returned", "Unit",
            "Returned By", "Reason for Return", "Condition", "Received By", "Photographic Record", "Remarks"
        ])
        returns_df.to_csv(RETURNS_CSV, index=False)

    returns_df = pd.read_csv(RETURNS_CSV)

    with st.form("returns_form"):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date", value=datetime.today())
            material_name = st.selectbox("Material Name", [
                "Cement", "Steel", "Sand", "Bricks", "Tiles", "Paint", "Other"])
            quantity = st.number_input("Quantity Returned", min_value=0.0)
            unit = st.selectbox("Unit", [
                "Bags", "Tons", "Liters", "Numbers", "Cubic Feet", "Cubic Meters"])
            returned_by = st.text_input("Returned By")

        with col2:
            reason = st.text_input("Reason for Return")
            condition = st.text_input("Material Condition")
            received_by = st.text_input("Received By")
            photo = st.file_uploader("Upload Photo (Optional)", type=["jpg", "jpeg", "png"])
            remarks = st.text_area("Remarks")

        submitted = st.form_submit_button("Submit")

        if submitted:
            photo_path = ""
            if photo:
                photo_path = os.path.join("data", photo.name)
                with open(photo_path, "wb") as f:
                    f.write(photo.read())

            new_return = {
                "Date": date.strftime("%Y-%m-%d"),
                "Material Name": material_name,
                "Quantity Returned": quantity,
                "Unit": unit,
                "Returned By": returned_by,
                "Reason for Return": reason,
                "Condition": condition,
                "Received By": received_by,
                "Photographic Record": photo_path,
                "Remarks": remarks
            }

            returns_df = pd.concat([returns_df, pd.DataFrame([new_return])], ignore_index=True)
            returns_df.to_csv(RETURNS_CSV, index=False)
            st.success("Return entry recorded!")

    st.subheader("📄 Returns Register Entries")
    st.dataframe(returns_df)
    st.download_button("⬇️ Download Returns Register", returns_df.to_csv(index=False), "returns_register.csv", "text/csv")

# === Damage / Loss Register ===
with tabs[4]:
    st.header("💥 Damage / Loss Register")

    DAMAGE_CSV = "data/damage_loss_register.csv"
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(DAMAGE_CSV):
        damage_df = pd.DataFrame(columns=[
            "Date", "Material Name", "Quantity", "Unit", "Reported By",
            "Location", "Cause", "Photographic Record", "Remarks"
        ])
        damage_df.to_csv(DAMAGE_CSV, index=False)

    damage_df = pd.read_csv(DAMAGE_CSV)

    with st.form("damage_loss_form"):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date", value=datetime.today())
            material_name = st.selectbox("Material Name", [
                "Cement", "Steel", "Sand", "Bricks", "Tiles", "Paint", "Other"])
            quantity = st.number_input("Quantity Damaged/Lost", min_value=0.0)
            unit = st.selectbox("Unit", [
                "Bags", "Tons", "Liters", "Numbers", "Cubic Feet", "Cubic Meters"])
            reported_by = st.text_input("Reported By")

        with col2:
            location = st.text_input("Location of Incident")
            cause = st.text_area("Cause of Damage or Loss")
            photo = st.file_uploader("Upload Photo (Optional)", type=["jpg", "jpeg", "png"])
            remarks = st.text_area("Additional Remarks")

        submitted = st.form_submit_button("Submit")

        if submitted:
            photo_path = ""
            if photo:
                photo_path = os.path.join("data", photo.name)
                with open(photo_path, "wb") as f:
                    f.write(photo.read())

            new_damage = {
                "Date": date.strftime("%Y-%m-%d"),
                "Material Name": material_name,
                "Quantity": quantity,
                "Unit": unit,
                "Reported By": reported_by,
                "Location": location,
                "Cause": cause,
                "Photographic Record": photo_path,
                "Remarks": remarks
            }

            damage_df = pd.concat([damage_df, pd.DataFrame([new_damage])], ignore_index=True)
            damage_df.to_csv(DAMAGE_CSV, index=False)
            st.success("Damage/Loss entry recorded!")

    st.subheader("📄 Damage / Loss Entries")
    st.dataframe(damage_df)
    st.download_button("⬇️ Download Damage Register", damage_df.to_csv(index=False), "damage_loss_register.csv", "text/csv")

# === Reconciliation ===
with tabs[5]:
    st.header("🧾 Material Reconciliation")

    RECONCILIATION_CSV = "data/reconciliation.csv"
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(RECONCILIATION_CSV):
        reconciliation_df = pd.DataFrame(columns=[
            "Date", "Material Name", "Total Received", "Total Issued",
            "Returned", "Damaged/Lost", "Balance", "Remarks"
        ])
        reconciliation_df.to_csv(RECONCILIATION_CSV, index=False)

    reconciliation_df = pd.read_csv(RECONCILIATION_CSV)

    with st.form("reconciliation_form"):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date", value=datetime.today())
            material_name = st.selectbox("Material Name", [
                "Cement", "Steel", "Sand", "Bricks", "Tiles", "Paint", "Other"])
            total_received = st.number_input("Total Received", min_value=0.0)
            total_issued = st.number_input("Total Issued", min_value=0.0)

        with col2:
            returned = st.number_input("Returned", min_value=0.0)
            damaged_lost = st.number_input("Damaged/Lost", min_value=0.0)
            remarks = st.text_area("Remarks (Optional)")

        submitted = st.form_submit_button("Submit")

        if submitted:
            balance = total_received - total_issued - damaged_lost + returned

            new_entry = {
                "Date": date.strftime("%Y-%m-%d"),
                "Material Name": material_name,
                "Total Received": total_received,
                "Total Issued": total_issued,
                "Returned": returned,
                "Damaged/Lost": damaged_lost,
                "Balance": balance,
                "Remarks": remarks
            }

            reconciliation_df = pd.concat([reconciliation_df, pd.DataFrame([new_entry])], ignore_index=True)
            reconciliation_df.to_csv(RECONCILIATION_CSV, index=False)
            st.success("Reconciliation entry saved.")

    st.subheader("📋 Reconciliation Entries")
    st.dataframe(reconciliation_df)
    st.download_button("⬇️ Download Reconciliation Report", reconciliation_df.to_csv(index=False), "reconciliation.csv", "text/csv")

# === Daily Closing ===
with tabs[6]:
    st.header("📅 Daily Closing Summary")

    DAILY_CLOSING_CSV = "data/daily_closing.csv"
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(DAILY_CLOSING_CSV):
        closing_df = pd.DataFrame(columns=[
            "Date", "Opening Stock", "Total Inward", "Total Outward",
            "Closing Stock", "Remarks"
        ])
        closing_df.to_csv(DAILY_CLOSING_CSV, index=False)

    closing_df = pd.read_csv(DAILY_CLOSING_CSV)

    with st.form("daily_closing_form"):
        date = st.date_input("Date", value=datetime.today())
        opening_stock = st.number_input("Opening Stock", min_value=0.0)
        total_inward = st.number_input("Total Inward", min_value=0.0)
        total_outward = st.number_input("Total Outward", min_value=0.0)
        remarks = st.text_area("Remarks")

        submitted = st.form_submit_button("Submit")

        if submitted:
            closing_stock = opening_stock + total_inward - total_outward

            new_entry = {
                "Date": date.strftime("%Y-%m-%d"),
                "Opening Stock": opening_stock,
                "Total Inward": total_inward,
                "Total Outward": total_outward,
                "Closing Stock": closing_stock,
                "Remarks": remarks
            }

            closing_df = pd.concat([closing_df, pd.DataFrame([new_entry])], ignore_index=True)
            closing_df.to_csv(DAILY_CLOSING_CSV, index=False)
            st.success("Daily closing entry saved.")

    st.subheader("📊 Daily Summary")
    st.dataframe(closing_df)
    st.download_button("⬇️ Download Daily Closing CSV", closing_df.to_csv(index=False), "daily_closing.csv", "text/csv")

# === Tab 8: Stock Summary ===
with tabs[7]:  # 8th tab (index starts at 0)
    st.header("📦 Stock Summary")

    # Helper to load CSV safely
    def load_csv_data(path):
        try:
            df = pd.read_csv(path)
            if "Material Name" not in df.columns or "Quantity" not in df.columns:
                return pd.DataFrame(columns=["Material Name", "Quantity"])
            return df
        except FileNotFoundError:
            return pd.DataFrame(columns=["Material Name", "Quantity"])

    inward_df = load_csv_data("data/inward.csv")
    outward_df = load_csv_data("data/outward.csv")
    returns_df = load_csv_data("data/returns.csv")
    damage_df = load_csv_data("data/damage.csv")

    # Summarize quantities
    inward_sum = inward_df.groupby("Material Name")["Quantity"].sum()
    outward_sum = outward_df.groupby("Material Name")["Quantity"].sum()
    returns_sum = returns_df.groupby("Material Name")["Quantity"].sum()
    damage_sum = damage_df.groupby("Material Name")["Quantity"].sum()

    # Union of all materials across registers
    all_materials = set(inward_sum.index) | set(outward_sum.index) | set(returns_sum.index) | set(damage_sum.index)

    summary_list = []
    for material in all_materials:
        inward = inward_sum.get(material, 0)
        outward = outward_sum.get(material, 0)
        returns = returns_sum.get(material, 0)
        damage = damage_sum.get(material, 0)

        available_stock = inward - outward - damage + returns

        summary_list.append({
            "Material Name": material,
            "Inward Qty": inward,
            "Outward Qty": outward,
            "Damage Qty": damage,
            "Return Qty": returns,
            "Available Stock": available_stock
        })

    summary_df = pd.DataFrame(summary_list)

    if not summary_df.empty and "Material Name" in summary_df.columns:
        st.dataframe(summary_df.sort_values(by="Material Name"))
    else:
        st.warning("No data available to display stock summary.")

# === Tab 9: BOQ Mapping ===
with tabs[8]:  # 9th tab (index starts at 0)
    st.header("📋 BOQ Mapping")

    boq_file = "data/boq_mapping.csv"

    # Load or initialize BOQ mapping
    if os.path.exists(boq_file):
        boq_df = pd.read_csv(boq_file)
    else:
        boq_df = pd.DataFrame(columns=[
            "Activity", "Material Name", "Unit",
            "Planned Qty", "Consumed Qty", "Balance Qty"
        ])

    st.dataframe(boq_df)

    with st.expander("➕ Add New BOQ Mapping Entry"):
        with st.form("boq_form"):
            activity = st.text_input("Activity / Task")
            material = st.selectbox("Material Name", material_options)
            unit = st.selectbox("Unit", unit_options)
            planned_qty = st.number_input("Planned Quantity", min_value=0.0, step=1.0)
            consumed_qty = st.number_input("Consumed Quantity", min_value=0.0, step=1.0)
            submitted = st.form_submit_button("Add Mapping")

            if submitted:
                balance_qty = planned_qty - consumed_qty
                new_entry = {
                    "Activity": activity,
                    "Material Name": material,
                    "Unit": unit,
                    "Planned Qty": planned_qty,
                    "Consumed Qty": consumed_qty,
                    "Balance Qty": balance_qty
                }
                boq_df = pd.concat([boq_df, pd.DataFrame([new_entry])], ignore_index=True)
                boq_df.to_csv(boq_file, index=False)
                st.success("BOQ Mapping entry added successfully.")
                st.experimental_rerun()

# === Tab 10: Indent Register ===
with tabs[9]:  # 10th tab (index starts at 0)
    st.header("📄 Indent Register")

    indent_file = "data/indent_register.csv"

    # Load or initialize indent register
    if os.path.exists(indent_file):
        indent_df = pd.read_csv(indent_file)
    else:
        indent_df = pd.DataFrame(columns=[
            "Indent ID", "Date & Time", "Requested By", "Department",
            "Material Name", "Unit", "Quantity", "Required Date", "Remarks", "Status"
        ])

    st.dataframe(indent_df)

    with st.expander("➕ Raise New Indent"):
        with st.form("indent_form"):
            indent_id = f"IND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            requested_by = st.text_input("Requested By")
            department = st.text_input("Department")
            material = st.selectbox("Material Name", material_options)
            unit = st.selectbox("Unit", unit_options)
            quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
            required_date = st.date_input("Required Date")
            remarks = st.text_area("Remarks")
            status = st.selectbox("Status", ["Pending", "Approved", "Fulfilled"])

            submitted = st.form_submit_button("Submit Indent")

            if submitted:
                new_indent = {
                    "Indent ID": indent_id,
                    "Date & Time": date_time,
                    "Requested By": requested_by,
                    "Department": department,
                    "Material Name": material,
                    "Unit": unit,
                    "Quantity": quantity,
                    "Required Date": required_date,
                    "Remarks": remarks,
                    "Status": status
                }
                indent_df = pd.concat([indent_df, pd.DataFrame([new_indent])], ignore_index=True)
                indent_df.to_csv(indent_file, index=False)
                st.success(f"Indent {indent_id} submitted successfully.")
                st.experimental_rerun()

# === Tab 11: Material Transfer Register ===
with tabs[10]:  # 11th tab (index starts at 0)
    st.header("🔄 Material Transfer Register")

    transfer_file = "data/material_transfer.csv"

    # Load or initialize transfer register
    if os.path.exists(transfer_file):
        transfer_df = pd.read_csv(transfer_file)
    else:
        transfer_df = pd.DataFrame(columns=[
            "Transfer ID", "Date & Time", "From Location", "To Location",
            "Material Name", "Unit", "Quantity", "Transferred By",
            "Approved By", "Vehicle No.", "Remarks"
        ])

    st.dataframe(transfer_df)

    with st.expander("➕ Log New Transfer"):
        with st.form("transfer_form"):
            transfer_id = f"MT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            from_loc = st.text_input("From Location")
            to_loc = st.text_input("To Location")
            material = st.selectbox("Material Name", material_options)
            unit = st.selectbox("Unit", unit_options)
            quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
            transferred_by = st.text_input("Transferred By")
            approved_by = st.text_input("Approved By")
            vehicle_no = st.text_input("Vehicle Number")
            remarks = st.text_area("Remarks")

            submitted = st.form_submit_button("Submit Transfer")

            if submitted:
                new_transfer = {
                    "Transfer ID": transfer_id,
                    "Date & Time": date_time,
                    "From Location": from_loc,
                    "To Location": to_loc,
                    "Material Name": material,
                    "Unit": unit,
                    "Quantity": quantity,
                    "Transferred By": transferred_by,
                    "Approved By": approved_by,
                    "Vehicle No.": vehicle_no,
                    "Remarks": remarks
                }
                transfer_df = pd.concat([transfer_df, pd.DataFrame([new_transfer])], ignore_index=True)
                transfer_df.to_csv(transfer_file, index=False)
                st.success(f"Transfer {transfer_id} recorded successfully.")
                st.experimental_rerun()

# === Tab 12: Scrap Register ===
with tabs[11]:  # 12th tab (index starts at 0)
    st.header("♻️ Scrap Register")

    scrap_file = "data/scrap_register.csv"

    # Load or initialize scrap register
    if os.path.exists(scrap_file):
        scrap_df = pd.read_csv(scrap_file)
    else:
        scrap_df = pd.DataFrame(columns=[
            "Scrap ID", "Date & Time", "Material Name", "Unit", "Quantity",
            "Source Location", "Reason for Scrap", "Approved By",
            "Disposal Method", "Remarks"
        ])

    st.dataframe(scrap_df)

    with st.expander("➕ Log Scrap Material"):
        with st.form("scrap_form"):
            scrap_id = f"SC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            material = st.selectbox("Material Name", material_options)
            unit = st.selectbox("Unit", unit_options)
            quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
            source_location = st.text_input("Source Location")
            reason = st.text_area("Reason for Scrap")
            approved_by = st.text_input("Approved By")
            disposal_method = st.text_input("Disposal Method (Sold / Stored / Reused / Disposed)")
            remarks = st.text_area("Remarks")

            submitted = st.form_submit_button("Submit Scrap Entry")

            if submitted:
                new_scrap = {
                    "Scrap ID": scrap_id,
                    "Date & Time": date_time,
                    "Material Name": material,
                    "Unit": unit,
                    "Quantity": quantity,
                    "Source Location": source_location,
                    "Reason for Scrap": reason,
                    "Approved By": approved_by,
                    "Disposal Method": disposal_method,
                    "Remarks": remarks
                }
                scrap_df = pd.concat([scrap_df, pd.DataFrame([new_scrap])], ignore_index=True)
                scrap_df.to_csv(scrap_file, index=False)
                st.success(f"Scrap entry {scrap_id} recorded successfully.")
                st.experimental_rerun()

# === Tab 13: Rate Contract Register ===
with tabs[12]:  # 13th tab (index starts at 0)
    st.header("📃 Rate Contract Register")

    contract_file = "data/rate_contract.csv"

    # Load or initialize rate contract register
    if os.path.exists(contract_file):
        contract_df = pd.read_csv(contract_file)
    else:
        contract_df = pd.DataFrame(columns=[
            "Contract ID", "Vendor Name", "Material Name", "Unit", "Rate",
            "Start Date", "End Date", "Remarks"
        ])

    st.dataframe(contract_df)

    with st.expander("➕ Add New Rate Contract"):
        with st.form("rate_contract_form"):
            contract_id = f"RC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            vendor_name = st.selectbox("Vendor Name", vendor_df["Vendor Name"].unique() if not vendor_df.empty else [])
            material_name = st.selectbox("Material Name", material_options)
            unit = st.selectbox("Unit", unit_options)
            rate = st.number_input("Rate", min_value=0.0, step=0.1)
            start_date = st.date_input("Start Date", value=datetime.today())
            end_date = st.date_input("End Date")
            remarks = st.text_area("Remarks")

            submitted = st.form_submit_button("Add Rate Contract")

            if submitted:
                new_contract = {
                    "Contract ID": contract_id,
                    "Vendor Name": vendor_name,
                    "Material Name": material_name,
                    "Unit": unit,
                    "Rate": rate,
                    "Start Date": start_date.strftime("%Y-%m-%d"),
                    "End Date": end_date.strftime("%Y-%m-%d"),
                    "Remarks": remarks
                }
                contract_df = pd.concat([contract_df, pd.DataFrame([new_contract])], ignore_index=True)
                contract_df.to_csv(contract_file, index=False)
                st.success(f"Rate contract {contract_id} added successfully.")
                st.experimental_rerun()









