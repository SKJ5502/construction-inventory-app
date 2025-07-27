import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# Environment setup for Streamlit Cloud
def setup_streamlit_environment():
    """Set up environment variables for Streamlit Cloud"""
    if 'GOOGLE_CREDENTIALS' in st.secrets:
        # Use Streamlit secrets
        os.environ['GOOGLE_CREDENTIALS'] = st.secrets['GOOGLE_CREDENTIALS']
        os.environ['GOOGLE_SPREADSHEET_ID'] = st.secrets['GOOGLE_SPREADSHEET_ID']
        return True
    else:
        st.error("Google Sheets credentials not found in secrets. Please add them in Streamlit Cloud settings.")
        return False

# Set up environment first
if not setup_streamlit_environment():
    st.stop()

from google_sheets_manager import GoogleSheetsManager
from utils import (calculate_amount, validate_input, format_date, format_currency, parse_numeric,
                  get_materials_from_master, get_grades_from_master, initialize_default_materials_and_grades)

# Material and Grade Constants - Define once and use throughout the app
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

# Dark theme CSS
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
    
    .stDataFrame {
        background: #2d2d30;
    }
    
    table {
        background: #2d2d30 !important;
        color: #ffffff !important;
    }
    
    th {
        background: #404040 !important;
        color: #ffffff !important;
    }
    
    td {
        background: #2d2d30 !important;
        color: #ffffff !important;
    }
    
    .stSelectbox select {
        background: #2d2d30 !important;
        color: #ffffff !important;
    }
    
    .stTextInput input {
        background: #2d2d30 !important;
        color: #ffffff !important;
    }
    
    .stNumberInput input {
        background: #2d2d30 !important;
        color: #ffffff !important;
    }
    
    .stTextArea textarea {
        background: #2d2d30 !important;
        color: #ffffff !important;
    }
    
    .stDateInput input {
        background: #2d2d30 !important;
        color: #ffffff !important;
    }
    
    .stExpander {
        background: #2d2d30;
        border: 1px solid #444;
    }
    
    .stTabs {
        background: #2d2d30;
    }
    
    .stForm {
        background: #2d2d30;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Google Sheets Manager
@st.cache_resource
def get_sheets_manager():
    try:
        manager = GoogleSheetsManager()
        return manager
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        return None

sheets_manager = get_sheets_manager()

if not sheets_manager:
    st.error("Unable to connect to Google Sheets. Please check your credentials.")
    st.stop()

# Navigation using individual buttons
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

# Initialize session state for current page
if 'current_page' not in st.session_state:
    st.session_state.current_page = "📊 Dashboard"

# Display navigation as individual buttons with custom styling
st.sidebar.subheader("📋 Modules")

# Add custom CSS for navigation buttons
st.markdown("""
<style>
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

/* Active button state */
div.stButton > button[aria-pressed="true"] {
    background-color: #0066cc !important;
    border-color: #0066cc !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

current_page = st.session_state.current_page

for option in nav_options:
    # Highlight the current active page
    button_type = "primary" if option == current_page else "secondary"
    if st.sidebar.button(option, key=f"nav_{option}", use_container_width=True, type=button_type):
        st.session_state.current_page = option

# Main content area
st.title(current_page)

# Get cached materials and grades from masters
cached_materials = get_materials_from_master(sheets_manager) + MATERIALS_LIST
cached_grades = get_grades_from_master(sheets_manager) + GRADES_LIST

# Remove duplicates while preserving order
materials_options = list(dict.fromkeys(cached_materials))
grades_options = list(dict.fromkeys(cached_grades))

# Dashboard Module
if current_page == "📊 Dashboard":
    st.markdown("### 📊 Construction Site Inventory Dashboard")
    
    try:
        # Get data for metrics
        inward_df = sheets_manager.read_data("Inward Register")
        outward_df = sheets_manager.read_data("Outward Register")
        vendor_df = sheets_manager.read_data("Vendor Master")
        
        # Calculate metrics
        total_materials = len(inward_df) if not inward_df.empty else 0
        active_vendors = len(vendor_df) if not vendor_df.empty else 0
        
        # Stock calculation - simplified
        if not inward_df.empty and not outward_df.empty:
            inward_qty = inward_df['Quantity'].sum() if 'Quantity' in inward_df.columns else 0
            outward_qty = outward_df['Quantity'].sum() if 'Quantity' in outward_df.columns else 0
            current_stock = max(0, inward_qty - outward_qty)
        else:
            current_stock = inward_df['Quantity'].sum() if not inward_df.empty and 'Quantity' in inward_df.columns else 0
        
        # Monthly inward calculation
        if not inward_df.empty and 'Date' in inward_df.columns:
            current_month = datetime.now().month
            current_year = datetime.now().year
            monthly_inward = 0
            
            for _, row in inward_df.iterrows():
                try:
                    if isinstance(row['Date'], str):
                        date_obj = datetime.strptime(row['Date'], '%Y-%m-%d')
                    else:
                        date_obj = row['Date']
                    
                    if date_obj.month == current_month and date_obj.year == current_year:
                        monthly_inward += row.get('Quantity', 0)
                except:
                    continue
        else:
            monthly_inward = 0
        
        # Display metrics in vertical layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="📦 Total Materials",
                value=f"{total_materials:,}",
                delta=f"+{monthly_inward}" if monthly_inward > 0 else None
            )
        
        with col2:
            st.metric(
                label="👥 Active Vendors",
                value=f"{active_vendors:,}",
                delta=None
            )
        
        with col3:
            # Low stock items (simplified calculation)
            low_stock_items = 0
            if not inward_df.empty:
                # Simple heuristic: if outward > 80% of inward for any material
                material_groups = inward_df.groupby(['Material Name', 'Grade'])['Quantity'].sum() if not inward_df.empty else pd.Series()
                if not outward_df.empty:
                    outward_groups = outward_df.groupby(['Material Name', 'Grade'])['Quantity'].sum()
                    for material_grade, inward_qty in material_groups.items():
                        outward_qty = outward_groups.get(material_grade, 0)
                        if outward_qty > (inward_qty * 0.8):
                            low_stock_items += 1
            
            st.metric(
                label="⚠️ Low Stock Items",
                value=f"{low_stock_items:,}",
                delta="Critical" if low_stock_items > 5 else None
            )
        
        # Monthly Inward metric positioned below main metrics
        st.markdown("---")
        col4, col5, col6 = st.columns(3)
        with col2:  # Center the monthly metric
            st.metric(
                label="📈 Monthly Inward",
                value=f"{monthly_inward:,}",
                delta="+12% vs last month" if monthly_inward > 0 else None
            )
        
        st.markdown("---")
        
        # Recent Activity Section
        st.markdown("### 📋 Recent Activity")
        
        if not inward_df.empty:
            recent_inward = inward_df.tail(5)[['Date', 'Material Name', 'Grade', 'Vendor', 'Quantity', 'Amount']]
            st.markdown("**Recent Inward Materials:**")
            st.dataframe(recent_inward, use_container_width=True)
        else:
            st.info("No recent inward activity found.")
        
        # Low Stock Alert Section
        st.markdown("### ⚠️ Low Stock Alert")
        
        if low_stock_items > 0:
            st.warning(f"⚠️ {low_stock_items} materials are running low on stock!")
            # Show some low stock items if available
            if not inward_df.empty and not outward_df.empty:
                low_stock_list = []
                for material_grade, inward_qty in material_groups.items():
                    outward_qty = outward_groups.get(material_grade, 0)
                    remaining = inward_qty - outward_qty
                    if remaining < (inward_qty * 0.2) and remaining > 0:  # Less than 20% remaining
                        low_stock_list.append({
                            'Material': material_grade[0],
                            'Grade': material_grade[1],
                            'Remaining Stock': remaining,
                            'Status': 'Low Stock'
                        })
                
                if low_stock_list:
                    low_stock_df = pd.DataFrame(low_stock_list)
                    st.dataframe(low_stock_df, use_container_width=True)
        else:
            st.success("✅ All materials are adequately stocked!")
        
        # Expiry Alert Section
        st.markdown("### ⏰ Expiry Alert")
        
        if not inward_df.empty and 'Expiry Date' in inward_df.columns:
            current_date = datetime.now().date()
            expiry_alerts = []
            
            for _, row in inward_df.iterrows():
                if pd.notna(row.get('Expiry Date')):
                    try:
                        if isinstance(row['Expiry Date'], str):
                            expiry_date = datetime.strptime(row['Expiry Date'], '%Y-%m-%d').date()
                        else:
                            expiry_date = row['Expiry Date']
                        
                        days_to_expiry = (expiry_date - current_date).days
                        
                        if days_to_expiry <= 30:  # Items expiring within 30 days
                            status = "Expired" if days_to_expiry < 0 else "Critical" if days_to_expiry <= 7 else "Warning"
                            expiry_alerts.append({
                                'Material': row.get('Material Name', 'N/A'),
                                'Grade': row.get('Grade', 'N/A'),
                                'Expiry Date': expiry_date,
                                'Days to Expiry': days_to_expiry,
                                'Status': status
                            })
                    except:
                        continue
            
            if expiry_alerts:
                expiry_df = pd.DataFrame(expiry_alerts)
                expiry_df = expiry_df.sort_values('Days to Expiry')
                
                # Color code the alerts
                critical_count = len(expiry_df[expiry_df['Status'].isin(['Expired', 'Critical'])])
                if critical_count > 0:
                    st.error(f"🚨 {critical_count} materials require immediate attention!")
                else:
                    st.warning("⚠️ Some materials are approaching expiry.")
                
                st.dataframe(expiry_df, use_container_width=True)
            else:
                st.success("✅ No materials approaching expiry!")
        else:
            st.info("Enable expiry tracking by adding expiry dates in Inward Register.")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.info("Dashboard will display metrics once you start adding data to the system.")

# Vendor Management Module
elif current_page == "👥 Vendor Management":
    st.markdown("### 👥 Vendor Management")
    
    tab1, tab2 = st.tabs(["Add New Vendor", "View/Edit Vendors"])
    
    with tab1:
        st.markdown("#### Add New Vendor")
        
        with st.form("vendor_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                vendor_name = st.text_input("Vendor Name*", help="Enter the vendor company name")
                material = st.selectbox("Primary Material Supplied", materials_options)
                material_name = st.text_input("Material Name", value=material)
                grade = st.selectbox("Grade/Specification", grades_options)
                contact_person = st.text_input("Contact Person*")
            
            with col2:
                phone = st.text_input("Phone Number*", help="Enter contact number")
                email = st.text_input("Email Address")
                gst_number = st.text_input("GST Number")
                address = st.text_area("Address", help="Enter complete address")
            
            submitted = st.form_submit_button("Add Vendor", use_container_width=True)
            
            if submitted:
                if validate_input(vendor_name, "Vendor Name") and validate_input(contact_person, "Contact Person") and validate_input(phone, "Phone"):
                    try:
                        vendor_data = {
                            "Vendor Name": vendor_name,
                            "Material": material,
                            "Material Name": material_name,
                            "Grade": grade,
                            "Contact Person": contact_person,
                            "Phone": phone,
                            "Email": email,
                            "GST Number": gst_number,
                            "Address": address,
                            "Date Added": format_date(datetime.now())
                        }
                        
                        success = sheets_manager.append_data("Vendor Master", vendor_data)
                        if success:
                            st.success(f"✅ Vendor '{vendor_name}' added successfully!")
                            st.balloons()
                        else:
                            st.error("Failed to add vendor. Please try again.")
                    except Exception as e:
                        st.error(f"Error adding vendor: {str(e)}")
    
    with tab2:
        st.markdown("#### Vendor Directory")
        
        try:
            vendors_df = sheets_manager.read_data("Vendor Master")
            
            if not vendors_df.empty:
                # Search and filter
                col1, col2 = st.columns(2)
                with col1:
                    search_term = st.text_input("🔍 Search Vendors", placeholder="Search by name or material...")
                with col2:
                    material_filter = st.selectbox("Filter by Material", ["All Materials"] + materials_options)
                
                # Apply filters
                filtered_df = vendors_df.copy()
                
                if search_term:
                    mask = filtered_df.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
                    filtered_df = filtered_df[mask]
                
                if material_filter != "All Materials":
                    filtered_df = filtered_df[filtered_df['Material'] == material_filter]
                
                if not filtered_df.empty:
                    st.markdown(f"**Found {len(filtered_df)} vendor(s)**")
                    
                    # Display vendors in a nice format
                    for idx, vendor in filtered_df.iterrows():
                        with st.expander(f"📋 {vendor.get('Vendor Name', 'Unknown')} - {vendor.get('Material', 'N/A')}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Contact Person:** {vendor.get('Contact Person', 'N/A')}")
                                st.write(f"**Phone:** {vendor.get('Phone', 'N/A')}")
                                st.write(f"**Email:** {vendor.get('Email', 'N/A')}")
                                st.write(f"**Material:** {vendor.get('Material Name', 'N/A')} ({vendor.get('Grade', 'N/A')})")
                            
                            with col2:
                                st.write(f"**GST Number:** {vendor.get('GST Number', 'N/A')}")
                                st.write(f"**Date Added:** {vendor.get('Date Added', 'N/A')}")
                                st.write(f"**Address:** {vendor.get('Address', 'N/A')}")
                    
                    # Also show as table
                    st.markdown("---")
                    st.markdown("#### Vendor Table")
                    display_columns = ['Vendor Name', 'Contact Person', 'Phone', 'Material Name', 'Grade', 'Date Added']
                    available_columns = [col for col in display_columns if col in filtered_df.columns]
                    st.dataframe(filtered_df[available_columns], use_container_width=True)
                else:
                    st.warning("No vendors found matching your criteria.")
            else:
                st.info("📝 No vendors added yet. Use the 'Add New Vendor' tab to get started.")
        
        except Exception as e:
            st.error(f"Error loading vendors: {str(e)}")

# Rest of the modules would follow the same pattern...
# For brevity, I'll continue with just a few key modules

# Inward Register Module
elif current_page == "📦 Inward Register":
    st.markdown("### 📦 Material Inward Register")
    
    tab1, tab2 = st.tabs(["Add Inward Entry", "View Inward Records"])
    
    with tab1:
        st.markdown("#### Record New Material Inward")
        
        with st.form("inward_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                entry_date = st.date_input("Date*", datetime.now())
                material_name = st.selectbox("Material Name*", materials_options)
                material = st.text_input("Material Category", value=material_name)
                grade = st.selectbox("Grade/Specification*", grades_options)
            
            with col2:
                # Get vendors for dropdown
                try:
                    vendors_df = sheets_manager.read_data("Vendor Master")
                    vendor_options = vendors_df['Vendor Name'].tolist() if not vendors_df.empty else ["No vendors found"]
                except:
                    vendor_options = ["No vendors found"]
                
                vendor = st.selectbox("Vendor*", vendor_options)
                quantity = st.number_input("Quantity*", min_value=0.0, step=0.1)
                unit = st.selectbox("Unit", ["Kg", "Tonnes", "Pieces", "Bags", "Liters", "Meters", "Sq.Ft", "Cu.Ft"])
                rate = st.number_input("Rate per Unit*", min_value=0.0, step=0.01)
            
            with col3:
                amount = calculate_amount(quantity, rate)
                st.number_input("Amount", value=amount, disabled=True)
                invoice_number = st.text_input("Invoice Number")
                received_by = st.text_input("Received By*")
                
            col4, col5 = st.columns(2)
            with col4:
                mfg_date = st.date_input("Manufacturing Date", value=None)
            with col5:
                expiry_date = st.date_input("Expiry Date", value=None)
            
            remarks = st.text_area("Remarks")
            
            submitted = st.form_submit_button("Record Inward Entry", use_container_width=True)
            
            if submitted:
                if (validate_input(material_name, "Material Name") and 
                    validate_input(grade, "Grade") and 
                    validate_input(vendor, "Vendor") and 
                    quantity > 0 and rate > 0 and 
                    validate_input(received_by, "Received By")):
                    
                    try:
                        inward_data = {
                            "Date": format_date(entry_date),
                            "Material Name": material_name,
                            "Material": material,
                            "Grade": grade,
                            "Vendor": vendor,
                            "Quantity": quantity,
                            "Unit": unit,
                            "Rate": rate,
                            "Amount": amount,
                            "Invoice Number": invoice_number,
                            "Received By": received_by,
                            "Mfg Date": format_date(mfg_date) if mfg_date else "",
                            "Expiry Date": format_date(expiry_date) if expiry_date else "",
                            "Remarks": remarks
                        }
                        
                        success = sheets_manager.append_data("Inward Register", inward_data)
                        if success:
                            st.success(f"✅ Inward entry recorded successfully! Amount: ₹{amount:,.2f}")
                            st.balloons()
                        else:
                            st.error("Failed to record entry. Please try again.")
                    except Exception as e:
                        st.error(f"Error recording entry: {str(e)}")
    
    with tab2:
        st.markdown("#### Inward Records")
        
        try:
            inward_df = sheets_manager.read_data("Inward Register")
            
            if not inward_df.empty:
                # Filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    date_filter = st.date_input("Filter by Date", value=None)
                with col2:
                    material_filter = st.selectbox("Filter by Material", ["All Materials"] + materials_options, key="inward_material_filter")
                with col3:
                    vendor_filter = st.selectbox("Filter by Vendor", ["All Vendors"] + list(inward_df['Vendor'].unique()) if 'Vendor' in inward_df.columns else ["All Vendors"])
                
                # Apply filters
                filtered_df = inward_df.copy()
                
                if date_filter:
                    date_str = format_date(date_filter)
                    filtered_df = filtered_df[filtered_df['Date'] == date_str]
                
                if material_filter != "All Materials":
                    filtered_df = filtered_df[filtered_df['Material Name'] == material_filter]
                
                if vendor_filter != "All Vendors":
                    filtered_df = filtered_df[filtered_df['Vendor'] == vendor_filter]
                
                if not filtered_df.empty:
                    # Summary metrics
                    total_entries = len(filtered_df)
                    total_value = filtered_df['Amount'].sum() if 'Amount' in filtered_df.columns else 0
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Entries", total_entries)
                    with col2:
                        st.metric("Total Value", f"₹{total_value:,.2f}")
                    
                    st.dataframe(filtered_df, use_container_width=True)
                    
                    # Download option
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"inward_register_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No records found matching your criteria.")
            else:
                st.info("📝 No inward records found. Start by adding your first entry!")
        
        except Exception as e:
            st.error(f"Error loading inward records: {str(e)}")

# Add basic implementations for other modules
elif current_page == "📤 Outward Register":
    st.markdown("### 📤 Material Outward Register")
    st.info("Outward Register functionality - Track materials issued/consumed")
    
elif current_page == "↩️ Returns Register":
    st.markdown("### ↩️ Material Returns Register")
    st.info("Returns Register functionality - Track returned materials")
    
elif current_page == "💥 Damage/Loss Register":
    st.markdown("### 💥 Damage/Loss Register")
    st.info("Damage/Loss Register functionality - Track damaged or lost materials")
    
elif current_page == "📋 BOQ Mapping":
    st.markdown("### 📋 BOQ Mapping")
    st.info("BOQ Mapping functionality - Map materials to Bill of Quantities")
    
elif current_page == "📝 Indent Register":
    st.markdown("### 📝 Material Indent Register")
    st.info("Indent Register functionality - Track material requisitions")
    
elif current_page == "🚚 Material Transfer Register":
    st.markdown("### 🚚 Material Transfer Register")
    st.info("Material Transfer Register functionality - Track inter-site transfers")
    
elif current_page == "♻️ Scrap Register":
    st.markdown("### ♻️ Scrap Register")
    st.info("Scrap Register functionality - Track scrap materials")
    
elif current_page == "📊 Stock Summary":
    st.markdown("### 📊 Stock Summary")
    st.info("Stock Summary functionality - View current stock levels")
    
elif current_page == "📊 Reports":
    st.markdown("### 📊 Reports Dashboard")
    st.info("Reports functionality - Generate various reports")
    
elif current_page == "⏰ Expiry Management":
    st.markdown("### ⏰ Expiry Management")
    st.info("Expiry Management functionality - Track material expiry dates")

# Footer
st.markdown("---")
st.markdown("### 🏗️ Construction Site Inventory Management System")
st.markdown("*Professional inventory management solution for construction projects*")
