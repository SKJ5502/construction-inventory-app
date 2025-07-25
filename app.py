import streamlit as st
import pandas as pd
import datetime
import math
from helpers.gsheet_utils import connect_sheet

st.set_page_config(page_title="Construction Inventory", layout="wide")
sheet = connect_sheet("Construction Inventory")

st.title("🏗️ Construction Site Inventory Management System")

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
    "Material Transfer",
    "Scrap Register",
    "Rate Contract",
    "PO Register",
    "Reports Dashboard",
    "User Management"
])

# === Vendor Management ===
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
        # Simulated master material list
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
        # Save file locally for this example
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
st.download_button("⬇️ Download Vendor Master",
                   df.to_csv(index=False),
                   "vendors.csv",
                   "text/csv")

# === Inward Register ===
with tabs[1]:
    st.header("📥 Inward Register")
    inward_df = pd.DataFrame(columns=[
        "Date", "Vendor Name", "Material", "Unit", "Quantity",
        "Rate", "Amount", "Expiry Date", "Photographic Record"
    ])
    st.dataframe(inward_df)
    st.info("Add inward form here...")

# === Outward Register ===
with tabs[2]:
    st.header("📤 Outward Register")
    outward_df = pd.DataFrame(columns=[
        "Date", "Material", "Unit", "Quantity", "Issued To",
        "Work Area", "BOQ Item", "Approved By"
    ])
    st.dataframe(outward_df)
    st.info("Add outward form here...")

# === Returns Register ===
with tabs[3]:
    st.header("🔄 Returns Register")
    returns_df = pd.DataFrame(columns=[
        "Date", "Return Type", "Material", "Unit", "Quantity",
        "Reason", "Approved By"
    ])
    st.dataframe(returns_df)
    st.info("Add returns form here...")

# === Damage / Loss ===
with tabs[4]:
    st.header("🚫 Damage / Loss Register")
    damage_df = pd.DataFrame(columns=[
        "Date", "Material", "Unit", "Quantity", "Type",
        "Reason", "Photo", "Approved By"
    ])
    st.dataframe(damage_df)
    st.info("Add damage/loss form here...")

# === Reconciliation ===
with tabs[5]:
    st.header("🧾 Reconciliation")
    rec_df = pd.DataFrame(columns=[
        "Date", "Material", "Unit", "Book Stock", "Physical Stock",
        "Variance", "Reason", "Approved By"
    ])
    st.dataframe(rec_df)
    st.info("Add reconciliation form here...")

# === Daily Closing ===
with tabs[6]:
    st.header("📅 Daily Closing")
    closing_df = pd.DataFrame(columns=[
        "Date", "Material", "Unit", "Opening Stock", "Inward",
        "Outward", "Returns", "Damage/Loss", "Adjustments",
        "Closing Stock (Book)", "Physical Stock", "Variance"
    ])
    st.dataframe(closing_df)
    st.info("Daily closing summary here...")

# === Stock Summary ===
with tabs[7]:
    st.header("📊 Stock Summary")
    stock_df = pd.DataFrame(columns=[
        "Material", "Unit", "Opening", "Inward", "Outward",
        "Returns", "Damage", "Current Stock", "Avg Rate", "Lowest Vendor"
    ])
    st.dataframe(stock_df)
    st.info("Live stock summary and charts here...")

# === BOQ Mapping ===
with tabs[8]:
    st.header("📐 BOQ Mapping")
    boq_df = pd.DataFrame(columns=[
        "Work Item", "Material", "Unit", "BOQ Qty",
        "Actual Issued", "Variance", "% Variance"
    ])
    st.dataframe(boq_df)
    st.info("Planned vs Actual mapping here...")

# === Indent Register ===
with tabs[9]:
    st.header("📝 Indent Register")
    indent_df = pd.DataFrame(columns=[
        "Date", "Indent Number", "Requested By", "Material",
        "Unit", "Qty Requested", "Qty Approved", "Approved By"
    ])
    st.dataframe(indent_df)
    st.info("Indent request/approval form here...")

# === Material Transfer ===
with tabs[10]:
    st.header("🔁 Material Transfer")
    transfer_df = pd.DataFrame(columns=[
        "Date", "From Site", "To Site", "Material",
        "Unit", "Quantity", "Approved By"
    ])
    st.dataframe(transfer_df)
    st.info("Material transfer register here...")

# === Scrap Register ===
with tabs[11]:
    st.header("♻️ Scrap Register")
    scrap_df = pd.DataFrame(columns=[
        "Date", "Material", "Unit", "Qty Scrap", "Disposal/Sold To",
        "Scrap Value", "Approved By"
    ])
    st.dataframe(scrap_df)
    st.info("Scrap tracking here...")

# === Rate Contract ===
with tabs[12]:
    st.header("💰 Rate Contract")
    rate_df = pd.DataFrame(columns=[
        "Vendor", "Material", "Unit", "Rate", "Valid From", "Valid To"
    ])
    st.dataframe(rate_df)
    st.info("Rate contracts details here...")

# === PO Register ===
with tabs[13]:
    st.header("📑 PO Register")
    po_df = pd.DataFrame(columns=[
        "PO Number", "Vendor", "Material", "Unit",
        "PO Qty", "Received Qty", "Balance Qty"
    ])
    st.dataframe(po_df)
    st.info("Purchase order register here...")

# === Reports Dashboard ===
with tabs[14]:
    st.header("📈 Reports & Dashboard")
    st.info("Charts, KPIs, and export options here...")

# === User Management ===
with tabs[15]:
    st.header("👤 User Management")
    st.info("Roles, access rights, audit log here...")
