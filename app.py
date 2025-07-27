import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# Environment setup for Streamlit Cloud - CRITICAL FIX
def setup_streamlit_environment():
    """Set up environment variables for Streamlit Cloud"""
    try:
        # Check if we're in Streamlit Cloud environment
        if hasattr(st, 'secrets'):
            if 'GOOGLE_CREDENTIALS' in st.secrets:
                # Use Streamlit secrets directly
                os.environ['GOOGLE_CREDENTIALS'] = str(st.secrets['GOOGLE_CREDENTIALS'])
                os.environ['GOOGLE_SPREADSHEET_ID'] = str(st.secrets['GOOGLE_SPREADSHEET_ID'])
                print("✅ Environment variables set from Streamlit secrets!")
                return True
        
        # Check if environment variables already exist (local development)
        if os.getenv('GOOGLE_CREDENTIALS') and os.getenv('GOOGLE_SPREADSHEET_ID'):
            print("✅ Using existing environment variables!")
            return True
        
        # If we reach here, credentials are missing
        st.error("🔑 Google Sheets credentials not found in Streamlit Cloud secrets.")
        st.info("Please add GOOGLE_CREDENTIALS and GOOGLE_SPREADSHEET_ID in your app settings.")
        return False
        
    except Exception as e:
        st.error(f"Error setting up environment: {str(e)}")
        return False

# Set up environment first - STOP if it fails
if not setup_streamlit_environment():
    st.stop()

# Import after environment setup
try:
    from google_sheets_manager import GoogleSheetsManager
    from utils import (calculate_amount, validate_input, format_date, format_currency, parse_numeric,
                      get_materials_from_master, get_grades_from_master, initialize_default_materials_and_grades)
except ImportError as e:
    st.error(f"Import error: {str(e)}")
    st.info("Please ensure all required files are uploaded to your repository.")
    st.stop()

# Material and Grade Constants
MATERIALS_LIST = [
    "Steel", "Cement", "Sand", "Gravel", "Bricks", "Tiles", "Paint", 
    "Wire", "Pipe", "Wood", "Glass", "Aluminum", "Concrete", "Marble",
    "Stone", "Plaster", "Bitumen", "Asphalt", "Ceramic", "Granite"
]

GRADES_LIST = [
    "8mm", "10mm", "12mm", "16mm", "20mm", "25mm", "32mm",
    "OPC 53", "OPC 43", "PPC", "PSC", 
    "Fine", "Coarse", "Medium",
    "20kg", "25kg", "40kg", "50kg",
    "5 Litre", "10 Litre", "20 Litre",
    "Grade A", "Grade B", "Premium", "Standard"
]

# Page configuration
st.set_page_config(
    page_title="Construction Site Inventory Management",
    page_icon="🏗️",
    layout="wide"
)

# Dark theme CSS with navigation styling
st.markdown("""
<style>
    .stApp {
        background: #1a1a1a;
        color: #ffffff;
    }
    
    * {
        color: #ffffff !important;
    }
    
    .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label {
        color: #ffffff !important;
    }
    
    input, select, textarea {
        background: #2d2d30 !important;
        color: #ffffff !important;
        border: 1px solid #555 !important;
    }
    
    .stButton button {
        background: #0066cc;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    
    .stButton button:hover {
        background: #0052a3;
    }
    
    .stMetric {
        background: #2d2d30;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #444;
    }
    
    /* Navigation button styling */
    div.stButton > button:first-child {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        width: 100% !important;
        padding: 0.5rem 1rem !important;
        margin: 0.1rem 0 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    div.stButton > button:first-child:hover {
        background-color: #2d2d2d !important;
        border-color: #555555 !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
    }

    div.stButton > button:first-child:active {
        background-color: #404040 !important;
        transform: translateY(0px) !important;
    }

    div.stButton > button[aria-pressed="true"] {
        background-color: #0066cc !important;
        border-color: #0066cc !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Google Sheets Manager with error handling
@st.cache_resource
def get_sheets_manager():
    try:
        manager = GoogleSheetsManager()
        if hasattr(manager, 'connected') and manager.connected:
            return manager
        else:
            st.error("Failed to connect to Google Sheets. Please check your credentials.")
            return None
    except Exception as e:
        st.error(f"Failed to initialize Google Sheets Manager: {str(e)}")
        return None

# Get the sheets manager
sheets_manager = get_sheets_manager()

# Stop execution if no connection
if not sheets_manager:
    st.error("🔌 Unable to connect to Google Sheets. Please check your configuration.")
    st.info("Make sure your secrets are properly configured in Streamlit Cloud settings.")
    st.stop()

# Navigation
st.sidebar.title("🏗️ Construction Inventory")

nav_options = [
    "📊 Dashboard",
    "👥 Vendor Management", 
    "📦 Inward Register",
    "📤 Outward Register",
    "↩️ Returns Register",
    "💥 Damage/Loss Register",
    "📋 BOQ Mapping",
    "📝 Indent Register",
    "🚚 Material Transfer Register",
    "♻️ Scrap Register",
    "📊 Stock Summary",
    "📊 Reports",
    "⏰ Expiry Management"
]

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "📊 Dashboard"

# Navigation buttons
st.sidebar.subheader("📋 Modules")

current_page = st.session_state.current_page

for option in nav_options:
    button_type = "primary" if option == current_page else "secondary"
    if st.sidebar.button(option, key=f"nav_{option}", use_container_width=True, type=button_type):
        st.session_state.current_page = option

# Main content
st.title(current_page)

# Get cached materials and grades
try:
    cached_materials = get_materials_from_master(sheets_manager) + MATERIALS_LIST
    cached_grades = get_grades_from_master(sheets_manager) + GRADES_LIST
    materials_options = list(dict.fromkeys(cached_materials))
    grades_options = list(dict.fromkeys(cached_grades))
except Exception as e:
    st.warning(f"Could not load cached materials: {str(e)}")
    materials_options = MATERIALS_LIST
    grades_options = GRADES_LIST

# Dashboard Module
if current_page == "📊 Dashboard":
    st.markdown("### 📊 Construction Site Inventory Dashboard")
    
    try:
        # Get data for metrics using correct method names
        inward_df = sheets_manager.get_inward_entries()
        outward_df = sheets_manager.get_outward_entries()
        vendor_df = sheets_manager.get_vendors()
        
        # Calculate metrics
        total_materials = len(inward_df) if not inward_df.empty else 0
        active_vendors = len(vendor_df) if not vendor_df.empty else 0
        
        # Stock calculation
        if not inward_df.empty and not outward_df.empty:
            inward_qty = inward_df['Quantity'].sum() if 'Quantity' in inward_df.columns else 0
            outward_qty = outward_df['Quantity'].sum() if 'Quantity' in outward_df.columns else 0
            current_stock = max(0, inward_qty - outward_qty)
        else:
            current_stock = inward_df['Quantity'].sum() if not inward_df.empty and 'Quantity' in inward_df.columns else 0
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📦 Total Materials", f"{total_materials:,}")
        with col2:
            st.metric("👥 Active Vendors", f"{active_vendors:,}")
        with col3:
            st.metric("⚠️ Low Stock Items", "0")
        
        # Recent activity
        st.markdown("---")
        st.markdown("### 📋 Recent Activity")
        
        if not inward_df.empty:
            recent_inward = inward_df.tail(5)
            st.dataframe(recent_inward, use_container_width=True)
        else:
            st.info("No recent activity found.")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

# Vendor Management Module
elif current_page == "👥 Vendor Management":
    st.markdown("### 👥 Vendor Management")
    
    tab1, tab2 = st.tabs(["Add New Vendor", "View Vendors"])
    
    with tab1:
        with st.form("vendor_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                vendor_name = st.text_input("Vendor Name*")
                material_supplied = st.selectbox("Material Supplied", materials_options)
                contact_person = st.text_input("Contact Person*")
            
            with col2:
                phone = st.text_input("Phone Number*")
                email = st.text_input("Email Address")
                address = st.text_area("Address")
            
            submitted = st.form_submit_button("Add Vendor", use_container_width=True)
            
            if submitted:
                if vendor_name and contact_person and phone:
                    try:
                        vendor_data = {
                            "Vendor Name": vendor_name,
                            "Material Supplied": material_supplied,
                            "Contact Person": contact_person,
                            "Phone": phone,
                            "Email": email,
                            "Address": address
                        }
                        
                        success = sheets_manager.add_vendor(vendor_data)
                        if success:
                            st.success(f"✅ Vendor '{vendor_name}' added successfully!")
                            st.balloons()
                        else:
                            st.error("Failed to add vendor. Please try again.")
                    except Exception as e:
                        st.error(f"Error adding vendor: {str(e)}")
    
    with tab2:
        try:
            vendors_df = sheets_manager.get_vendors()
            
            if not vendors_df.empty:
                st.dataframe(vendors_df, use_container_width=True)
            else:
                st.info("No vendors added yet.")
        except Exception as e:
            st.error(f"Error loading vendors: {str(e)}")

# Inward Register Module
elif current_page == "📦 Inward Register":
    st.markdown("### 📦 Material Inward Register")
    
    tab1, tab2 = st.tabs(["Add Inward Entry", "View Records"])
    
    with tab1:
        with st.form("inward_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                entry_date = st.date_input("Date*", datetime.now())
                material = st.selectbox("Material*", materials_options)
                
            with col2:
                try:
                    vendors_df = sheets_manager.get_vendors()
                    vendor_options = vendors_df['Vendor Name'].tolist() if not vendors_df.empty else ["No vendors found"]
                except:
                    vendor_options = ["No vendors found"]
                
                vendor = st.selectbox("Vendor*", vendor_options)
                quantity = st.number_input("Quantity*", min_value=0.0, step=0.1)
            
            with col3:
                unit = st.selectbox("Unit", ["Kg", "Tonnes", "Pieces", "Bags", "Liters"])
                rate = st.number_input("Rate per Unit*", min_value=0.0, step=0.01)
                amount = quantity * rate
                st.number_input("Amount", value=amount, disabled=True)
            
            col4, col5 = st.columns(2)
            with col4:
                invoice_number = st.text_input("Invoice Number")
                received_by = st.text_input("Received By*")
            with col5:
                expiry_date = st.date_input("Expiry Date", value=None)
                remarks = st.text_area("Remarks")
            
            submitted = st.form_submit_button("Record Entry", use_container_width=True)
            
            if submitted:
                if material and vendor and quantity > 0 and rate > 0 and received_by:
                    try:
                        inward_data = {
                            "Date": format_date(entry_date),
                            "Material": material,
                            "Vendor Name": vendor,
                            "Quantity": quantity,
                            "Unit": unit,
                            "Rate per Unit": rate,
                            "Amount": amount,
                            "Invoice Number": invoice_number,
                            "Received By": received_by,
                            "Remarks": remarks,
                            "Expiry Date": format_date(expiry_date) if expiry_date else ""
                        }
                        
                        success = sheets_manager.add_inward_entry(inward_data)
                        if success:
                            st.success(f"✅ Entry recorded! Amount: ₹{amount:,.2f}")
                            st.balloons()
                        else:
                            st.error("Failed to record entry.")
                    except Exception as e:
                        st.error(f"Error recording entry: {str(e)}")
    
    with tab2:
        try:
            inward_df = sheets_manager.get_inward_entries()
            
            if not inward_df.empty:
                st.dataframe(inward_df, use_container_width=True)
            else:
                st.info("No inward records found.")
        except Exception as e:
            st.error(f"Error loading records: {str(e)}")

# Other modules with basic placeholders
else:
    st.info(f"{current_page} functionality - Coming soon!")

# Footer
st.markdown("---")
st.markdown("### 🏗️ Construction Site Inventory Management System")
st.markdown("*Professional inventory management for construction projects*")
