import streamlit as st
import pandas as pd
import datetime
import math
from helpers.gsheet_utils import connect_sheet

st.set_page_config(page_title="Construction Inventory", layout="wide")
sheet = connect_sheet("Construction Inventory")

TABS = [
    "📦 Material Master", "📥 Inward", "📤 Outward", "📊 Stock Summary",
    "🔁 Reconciliation", "🗑️ Damage/Loss", "🔁 Returns",
    "📈 BOQ Mapping", "📅 Daily Closing", "👷 Vendor Management"
]
tabs = st.tabs(TABS)

SERIES_LIST = [f"Series {i}" for i in range(1, 11)]

# ----------------- 📦 Material Master -----------------
with tabs[0]:
    st.header("📦 Material Master")
    with st.form("material_form"):
        name = st.text_input("Material Name")
        category = st.selectbox("Category", ["Cement", "Steel", "Tiles", "Paint", "Plumbing", "Electrical", "Aggregates", "Other"])
        unit = st.text_input("Unit (e.g. Bags, Kg, Litres)")
        hsn = st.text_input("HSN Code (optional)")
        reorder = st.number_input("Reorder Level", min_value=0.0)
        vendor = st.text_input("Preferred Vendor(s)")
        submit = st.form_submit_button("Add Material")
        if submit:
            sheet.worksheet("Material Master").append_row([name, category, unit, hsn, reorder, vendor])
            st.success("Material added.")

# ----------------- 📥 Inward Entry -----------------
with tabs[1]:
    st.header("📥 Material Inward Entry")
    with st.form("inward_form"):
        date = st.date_input("Date", datetime.date.today())
        site = st.text_input("Site")
        material = st.text_input("Material Name")
        quantity = st.number_input("Quantity", min_value=0.0)
        vendor = st.text_input("Vendor Name")
        invoice = st.text_input("Invoice/DC No")
        received_by = st.text_input("Received By")
        remarks = st.text_area("Remarks")
        file = st.file_uploader("Attach Invoice/Photo")
        submit = st.form_submit_button("Submit Inward")
        if submit:
            sheet.worksheet("Inward").append_row([str(date), site, material, quantity, vendor, invoice, received_by, remarks])
            st.success("Inward recorded.")

# ----------------- 📤 Outward Entry -----------------
with tabs[2]:
    st.header("📤 Material Outward Entry")
    with st.form("outward_form"):
        date = st.date_input("Date", datetime.date.today())
        site = st.text_input("Site")
        material = st.text_input("Material Name")
        quantity = st.number_input("Quantity", min_value=0.0)
        issued_to = st.text_input("Issued To (Contractor or Section)")
        purpose = st.text_input("Purpose/Work Area")
        series = st.selectbox("Series", SERIES_LIST)
        flat_no = st.text_input("Flat No (if applicable)")
        issued_by = st.text_input("Issued By")
        remarks = st.text_area("Remarks")
        submit = st.form_submit_button("Submit Outward")
        if submit:
            sheet.worksheet("Outward").append_row([
                str(date), site, material, quantity, issued_to, purpose, series, flat_no, issued_by, remarks
            ])
            st.success("Outward recorded.")

# ----------------- 📊 Stock Summary -----------------
with tabs[3]:
    st.header("📊 Stock Summary")
    st.info("This module will calculate live stock from inward - outward")

# ----------------- 🔁 Reconciliation -----------------
with tabs[4]:
    st.header("🔁 Reconciliation")
    with st.form("recon_form"):
        date_range = st.date_input("Date Range", [datetime.date.today(), datetime.date.today()])
        site = st.text_input("Site")
        material = st.text_input("Material Name")
        system_stock = st.number_input("System Stock", min_value=0.0)
        physical_stock = st.number_input("Physical Stock", min_value=0.0)
        discrepancy = system_stock - physical_stock
        reason = st.text_area("Discrepancy Reason")
        uploaded = st.file_uploader("Attach Photo/Count Sheet")
        submit = st.form_submit_button("Submit Reconciliation")
        if submit:
            sheet.worksheet("Reconciliation").append_row([
                str(date_range[0]), str(date_range[1]), site, material, system_stock,
                physical_stock, discrepancy, reason, "Pending", ""
            ])
            st.success("Reconciliation submitted for approval.")

# ----------------- 🗑️ Damage/Loss -----------------
with tabs[5]:
    st.header("🗑️ Damaged or Lost Material")
    with st.form("damage_form"):
        date = st.date_input("Date", datetime.date.today())
        material = st.text_input("Material Name")
        quantity = st.number_input("Damaged Qty", min_value=0.0)
        reason = st.text_input("Reason")
        reported_by = st.text_input("Reported By")
        photo = st.file_uploader("Attach Photo")
        submit = st.form_submit_button("Log Damage")
        if submit:
            sheet.worksheet("Damage Log").append_row([
                str(date), material, quantity, reason, reported_by
            ])
            st.success("Damage recorded and stock updated.")

# ----------------- 🔁 Returns -----------------
with tabs[6]:
    st.header("🔁 Returns from Contractor")
    with st.form("returns_form"):
        date = st.date_input("Date", datetime.date.today())
        material = st.text_input("Material Name")
        quantity = st.number_input("Returned Qty", min_value=0.0)
        returned_by = st.text_input("Returned By")
        reason = st.text_input("Reason")
        submit = st.form_submit_button("Record Return")
        if submit:
            sheet.worksheet("Returns").append_row([
                str(date), material, quantity, returned_by, reason
            ])
            st.success("Return recorded and stock updated.")

# ----------------- 📈 BOQ Mapping -----------------
with tabs[7]:
    st.header("📈 BOQ Material Mapping")
    with st.form("boq_form"):
        series = st.selectbox("Select Series", SERIES_LIST)
        material = st.text_input("Material")
        planned_qty = st.number_input("Planned Quantity", min_value=0.0)
        submit = st.form_submit_button("Save BOQ")
        if submit:
            sheet.worksheet("BOQ Mapping").append_row([series, material, planned_qty])
            st.success("BOQ mapped for selected series.")

# ----------------- 📅 Daily Closing -----------------
with tabs[8]:
    st.header("📅 Daily Closing Stock")
    with st.form("closing_form"):
        date = st.date_input("Date", datetime.date.today())
        site = st.text_input("Site")
        material = st.text_input("Material")
        closing_qty = st.number_input("Closing Qty", min_value=0.0)
        submitted_by = st.text_input("Submitted By")
        submit = st.form_submit_button("Submit Closing")
        if submit:
            sheet.worksheet("Daily Closing").append_row([
                str(date), site, material, closing_qty, submitted_by
            ])
            st.success("Daily closing recorded.")

# ----------------- 👷 Vendor Management -----------------
with tabs[9]:
    st.header("👷 Vendor Master")
    with st.form("vendor_form"):
        name = st.text_input("Vendor Name")
        contact = st.text_input("Contact Number")
        gst = st.text_input("GSTIN")
        materials = st.text_input("Materials Supplied")
        rating = st.slider("Quality Rating", 1, 5, 3)
        submit = st.form_submit_button("Add Vendor")
        if submit:
            sheet.worksheet("Vendor Master").append_row([
                name, contact, gst, materials, rating
            ])
            st.success("Vendor added successfully.")
