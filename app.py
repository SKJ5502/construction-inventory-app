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
SHEET_NAME = "Construction Inventory"
VENDOR_SHEET = "Vendor Master"
# === Function to connect to Google Sheet and load vendor data ===
def load_vendor_data():
    try:
        worksheet = client.open(SHEET_NAME).worksheet(VENDOR_SHEET)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        # Force all column names to string before stripping
        df.columns = df.columns.map(lambda x: str(x).strip())

        return worksheet, df
    except Exception as e:
        st.error(f"Error loading Vendor Master sheet: {e}")
        return None, pd.DataFrame()

# === Function to write vendor data back to Google Sheet ===
def save_vendor_data(worksheet, df):
    try:
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
    except Exception as e:
        st.error(f"Failed to write to Google Sheet: {e}")

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
    st.header("📦 Vendor Management")

    vendor_ws, vendor_df = load_vendor_data()

    # === Vendor Input Form ===
    with st.form("vendor_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Vendor Name")
            material = st.text_input("Material Supplied")
            contact = st.text_input("Contact Person")
        with col2:
            phone = st.text_input("Phone Number")
            email = st.text_input("Email")
            address = st.text_area("Address")

        submitted = st.form_submit_button("Add Vendor")

        if submitted:
            if name.strip() == "":
                st.warning("Vendor Name is required.")
            else:
                new_vendor = {
                    "Vendor Name": name.strip(),
                    "Material Supplied": material,
                    "Contact Person": contact,
                    "Phone": phone,
                    "Email": email,
                    "Address": address
                }

                vendor_df = pd.concat([vendor_df, pd.DataFrame([new_vendor])], ignore_index=True)
                save_vendor_data(vendor_ws, vendor_df)
                st.success("Vendor added successfully!")

    # === Display Vendor Table ===
    st.subheader("📄 Existing Vendors")
    if not vendor_df.empty:
        st.dataframe(vendor_df)

        with st.expander("🗑️ Delete Vendor"):
            with st.form("delete_vendor_form"):
                delete_name = st.selectbox("Select Vendor to Delete", vendor_df["Vendor Name"].unique())
                delete_submitted = st.form_submit_button("Delete Vendor")

                if delete_submitted:
                    vendor_df = vendor_df[vendor_df["Vendor Name"] != delete_name]
                    save_vendor_data(vendor_ws, vendor_df)
                    st.success(f"Vendor '{delete_name}' deleted.")
    else:
        st.info("No vendor data available.")


# === Inward Register ===
# Load vendor names from Vendor Master worksheet
def load_vendor_names():
    try:
        ws = client.open(SHEET_NAME).worksheet("Vendor Master")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if "Vendor Name" in df.columns:
            return df["Vendor Name"].dropna().unique().tolist()
        else:
            return []
    except Exception as e:
        st.error(f"Error loading Vendor Master: {e}")
        return []
with tabs[1]:
    st.header("📥 Inward Register")

    inward_ws, inward_df = load_worksheet("Inward Register")  # Your helper function

    with st.form("inward_form"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", value=datetime.date.today())
            material = st.text_input("Material")
            vendor_name = st.selectbox("Vendor Name", load_vendor_names())
            quantity = st.number_input("Quantity", min_value=0.0, step=0.01)
            unit = st.text_input("Unit")
        with col2:
            rate = st.number_input("Rate per Unit", min_value=0.0, step=0.01)
            amount = quantity * rate
            st.markdown(f"**Amount:** ₹ {amount:,.2f}")
            invoice = st.text_input("Invoice Number")
            received_by = st.text_input("Received By")
            remarks = st.text_area("Remarks")
            expiry_date = st.date_input("Expiry Date")

        submitted = st.form_submit_button("Submit Entry")

        if submitted:
            new_entry = {
                "Date": date.strftime("%Y-%m-%d"),
                "Material": material,
                "Vendor Name": vendor_name,
                "Quantity": quantity,
                "Unit": unit,
                "Rate per Unit": rate,
                "Amount": amount,
                "Invoice Number": invoice,
                "Received By": received_by,
                "Remarks": remarks,
                "Expiry Date": expiry_date.strftime("%Y-%m-%d"),
            }

            # Append and save
            inward_df = pd.concat([inward_df, pd.DataFrame([new_entry])], ignore_index=True)
            save_worksheet(inward_ws, inward_df)  # Your write function
            st.success("Inward entry recorded successfully!")

    # === Display Table ===
    st.subheader("📄 Inward Register Entries")
    st.dataframe(inward_df)
    st.download_button("⬇️ Download Inward Register", inward_df.to_csv(index=False), "inward_register.csv", "text/csv")



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
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to record entry: {e}")

    st.subheader("📄 Outward Register Entries")
    if not outward_df.empty:
        st.dataframe(outward_df)
        st.download_button("⬇️ Download Outward Register", outward_df.to_csv(index=False), "outward_register.csv", "text/csv")
    else:
        st.info("No outward entries found.")

# === Returns Register ===
with tabs[3]:
    st.header("🔁 Returns Register")

    try:
        worksheet = client.open(SHEET_NAME).worksheet("Returns Register")
        returns_df = pd.DataFrame(worksheet.get_all_records())
    except Exception as e:
        st.error(f"Error loading Returns Register: {e}")
        returns_df = pd.DataFrame(columns=[
            "Date", "Material Name", "Quantity Returned", "Unit",
            "Returned By", "Reason for Return", "Condition",
            "Received By", "Photographic Record", "Remarks"
        ])

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
                os.makedirs("data", exist_ok=True)
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

            try:
                worksheet.append_row(list(new_return.values()))
                st.success("✅ Return entry recorded!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to record entry: {e}")

    st.subheader("📄 Returns Register Entries")
    if not returns_df.empty:
        st.dataframe(returns_df)
        st.download_button("⬇️ Download Returns Register", returns_df.to_csv(index=False), "returns_register.csv", "text/csv")
    else:
        st.info("No returns recorded yet.")

# === Damage / Loss Register ===
with tabs[4]:
    st.header("💥 Damage / Loss Register")

    try:
        worksheet = client.open(SHEET_NAME).worksheet("Damage Loss Register")
        damage_df = pd.DataFrame(worksheet.get_all_records())
    except Exception as e:
        st.error(f"Error loading Damage Loss Register: {e}")
        damage_df = pd.DataFrame(columns=[
            "Date", "Material Name", "Quantity", "Unit", "Reported By",
            "Location", "Cause", "Photographic Record", "Remarks"
        ])

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
                os.makedirs("data", exist_ok=True)
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

            try:
                worksheet.append_row(list(new_damage.values()))
                st.success("✅ Damage/Loss entry recorded!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to record entry: {e}")

    st.subheader("📄 Damage / Loss Entries")
    if not damage_df.empty:
        st.dataframe(damage_df)
        st.download_button("⬇️ Download Damage Register", damage_df.to_csv(index=False), "damage_loss_register.csv", "text/csv")
    else:
        st.info("No damage or loss entries yet.")






























