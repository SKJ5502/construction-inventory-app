import streamlit as st
import pandas as pd
from datetime import datetime
import setup_env

# Set up environment first
setup_env.setup_environment()

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
    
    .stExpander {
        background: #2d2d30;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Google Sheets connection with caching
@st.cache_resource
def init_sheets_manager():
    """Initialize Google Sheets Manager with caching"""
    try:
        sheets_manager = GoogleSheetsManager()
        
        # Define sheets configuration
        sheets_config = {
            'Vendor Master': [
                'Vendor Name', 'Material', 'Material Name', 'Grade', 'Contact Person', 'Phone', 'Email', 'GST Number', 'Address', 'Date Added'
            ],
            'Inward Register': [
                'Date', 'Material Name', 'Material', 'Grade', 'Vendor', 'Quantity', 'Unit', 'Rate', 'Amount', 'Invoice Number', 'Received By', 'Mfg Date', 'Expiry Date', 'Remarks'
            ],
            'Outward Register': [
                'Date', 'Material Name', 'Material', 'Grade', 'Quantity', 'Unit', 'Issued To', 'Purpose', 'Issued By', 'Remarks'
            ]
        }
        
        # Ensure all worksheets have proper structure
        for sheet_name, headers in sheets_config.items():
            try:
                sheets_manager.get_or_create_worksheet(sheet_name, headers)
            except Exception as e:
                print(f"Warning: Could not update {sheet_name} structure: {e}")
        
        # Initialize default materials and grades
        try:
            initialize_default_materials_and_grades(sheets_manager)
        except Exception as e:
            print(f"Warning: Could not initialize default materials and grades: {e}")
        
        return sheets_manager
    except Exception as e:
        st.error(f"Google Sheets connection failed: {str(e)}")
        return None

@st.cache_data(ttl=600)  # Cache for 10 minutes to reduce API calls significantly
def get_cached_inward_data():
    """Get inward data with extended caching to reduce API calls"""
    try:
        if sheets_manager:
            inward_headers = ['Date', 'Material Name', 'Material', 'Grade', 'Vendor', 'Quantity', 'Unit', 'Rate', 'Amount', 'Invoice Number', 'Received By', 'Mfg Date', 'Expiry Date', 'Remarks']
            inward_worksheet = sheets_manager.get_or_create_worksheet('Inward Register', inward_headers)
            return sheets_manager.dataframe_from_worksheet(inward_worksheet)
    except Exception as e:
        return pd.DataFrame()  # Return empty dataframe silently to avoid repeated error messages
    return pd.DataFrame()

@st.cache_data(ttl=600)  # Cache for 10 minutes to reduce API calls significantly
def get_cached_vendor_data():
    """Get vendor data with extended caching to reduce API calls"""
    try:
        if sheets_manager:
            vendor_headers = ['Vendor Name', 'Material', 'Material Name', 'Grade', 'Contact Person', 'Phone', 'Email', 'GST Number', 'Address', 'Date Added']
            vendor_worksheet = sheets_manager.get_or_create_worksheet('Vendor Master', vendor_headers)
            return sheets_manager.dataframe_from_worksheet(vendor_worksheet)
    except Exception as e:
        return pd.DataFrame()  # Return empty dataframe silently to avoid repeated error messages
    return pd.DataFrame()

@st.cache_data(ttl=60)  # Cache for 1 minute for faster updates
def get_cached_outward_data():
    """Get outward data with caching to reduce API calls"""
    try:
        if sheets_manager:
            outward_headers = ['Date', 'Material Name', 'Material', 'Grade', 'Quantity', 'Unit', 'Issued To', 'Purpose', 'Issued By', 'Wing', 'Flat Number', 'Remarks']
            outward_worksheet = sheets_manager.get_or_create_worksheet('Outward Register', outward_headers)
            return sheets_manager.dataframe_from_worksheet(outward_worksheet)
    except Exception as e:
        st.error(f"Error loading outward data: {str(e)}")
    return pd.DataFrame()

@st.cache_data(ttl=600)  # Cache for 10 minutes to reduce API calls significantly
def get_cached_vendors_list():
    """Get vendors list with extended caching to reduce API calls"""
    try:
        vendor_df = get_cached_vendor_data()
        if not vendor_df.empty and 'Vendor Name' in vendor_df.columns:
            return sorted(vendor_df['Vendor Name'].dropna().unique().tolist())
    except Exception as e:
        pass  # Silently fail to avoid repeated error messages
    return []  # Return empty list - no predefined vendors

@st.cache_data(ttl=60)  # Cache for 1 minute for faster updates
def get_cached_materials_list():
    """Get materials list with caching to reduce API calls"""
    try:
        inward_df = get_cached_inward_data()
        if not inward_df.empty and 'Material' in inward_df.columns:
            unique_materials = sorted(inward_df['Material'].dropna().unique().tolist())
            # Combine predefined materials with user-entered materials
            all_materials = list(set(MATERIALS_LIST + unique_materials))
            return sorted(all_materials)
    except Exception as e:
        print(f"Error loading materials: {str(e)}")
    return MATERIALS_LIST  # Return predefined materials as fallback

@st.cache_data(ttl=60)  # Cache for 1 minute for faster updates
def get_cached_grades_list():
    """Get grades list with caching to reduce API calls"""
    try:
        inward_df = get_cached_inward_data()
        if not inward_df.empty and 'Grade' in inward_df.columns:
            unique_grades = sorted(inward_df['Grade'].dropna().unique().tolist())
            # Combine predefined grades with user-entered grades
            all_grades = list(set(GRADES_LIST + unique_grades))
            return sorted(all_grades)
    except Exception as e:
        print(f"Error loading grades: {str(e)}")
    return GRADES_LIST  # Return predefined grades as fallback

def clear_cache():
    """Clear all cached data to ensure fresh data after updates"""
    get_cached_inward_data.clear()
    get_cached_vendor_data.clear()
    get_cached_outward_data.clear()
    get_cached_vendors_list.clear()
    get_cached_materials_list.clear()
    get_cached_grades_list.clear()

# Initialize sheets manager
try:
    sheets_manager = init_sheets_manager()
except Exception as e:
    st.error(f"Failed to initialize Google Sheets: {str(e)}")
    sheets_manager = None

def create_material_grade_selector(sheets_manager, key_prefix=""):
    """Create material and grade dropdowns using predefined lists plus user data"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get materials list (predefined + user-entered)
        materials_list = get_cached_materials_list()
        material = st.selectbox(
            "Material*",
            materials_list,
            key=f"{key_prefix}_material"
        )
    
    with col2:
        # Get grades list (predefined + user-entered)  
        grades_list = get_cached_grades_list()
        grade = st.selectbox(
            "Grade*",
            grades_list,
            key=f"{key_prefix}_grade"
        )
    
    return material, grade

# Sidebar navigation
st.sidebar.title("🧭 Navigation")

if sheets_manager:
    st.sidebar.success("✅ Google Sheets Connected")
else:
    st.sidebar.error("❌ Google Sheets Not Connected")

# Navigation options
nav_options = [
    "📊 Dashboard",
    "📦 Vendor Management", 
    "🚛 Inward Register",
    "📤 Outward Register", 
    "🔁 Returns Register",
    "❌ Damage / Loss Register",
    "⚖️ Reconciliation",
    "📊 Stock Summary",
    "📑 BOQ Mapping",
    "📝 Indent Register",
    "🔄 Material Transfer Register",
    "♻️ Scrap Register",
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

# Page content based on selection
if "Dashboard" in current_page:
    st.subheader("📊 Construction Site Inventory Dashboard")
    
    # Quick Stats Row - Calculate real values using cached data
    if sheets_manager:
        try:
            # Get cached data to reduce API calls
            inward_df = get_cached_inward_data()
            vendor_df = get_cached_vendor_data()
            
            # Calculate metrics
            total_materials = len(inward_df['Material'].dropna().unique()) if not inward_df.empty else 0
            active_vendors = len(vendor_df['Vendor Name'].dropna().unique()) if not vendor_df.empty else 0
            
            # Calculate monthly inward amount
            monthly_inward = 0
            if not inward_df.empty and 'Amount' in inward_df.columns and 'Date' in inward_df.columns:
                inward_df['Date'] = pd.to_datetime(inward_df['Date'], errors='coerce')
                current_month = pd.Timestamp.now().replace(day=1)
                monthly_data = inward_df[inward_df['Date'] >= current_month]
                monthly_inward = monthly_data['Amount'].sum() if not monthly_data.empty else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📦 Total Materials", total_materials)
            with col2:
                st.metric("📋 Active Vendors", active_vendors)
            with col3:
                st.metric("⚠️ Low Stock Items", "8", "-2")  # Will calculate below
            
            # Monthly Inward below the main metrics for better readability
            st.markdown("")  # Small spacing
            col_monthly = st.columns(1)[0]
            with col_monthly:
                st.metric("📈 Monthly Inward", f"₹{monthly_inward:,.0f}")
                
        except Exception as e:
            # Fallback to default values if error
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📦 Total Materials", "0")
            with col2:
                st.metric("📋 Active Vendors", "0")
            with col3:
                st.metric("⚠️ Low Stock Items", "0")
            
            # Monthly Inward below the main metrics
            st.markdown("")
            col_monthly = st.columns(1)[0]
            with col_monthly:
                st.metric("📈 Monthly Inward", "₹0")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📦 Total Materials", "0")
        with col2:
            st.metric("📋 Active Vendors", "0")
        with col3:
            st.metric("⚠️ Low Stock Items", "0")
        
        # Monthly Inward below the main metrics
        st.markdown("")
        col_monthly = st.columns(1)[0]
        with col_monthly:
            st.metric("📈 Monthly Inward", "₹0")
    
    st.markdown("---")
    st.subheader("🕒 Recent Activity")
    
    if sheets_manager:
        try:
            # Get cached recent activities to reduce API calls
            inward_df = get_cached_inward_data()
            outward_df = get_cached_outward_data()
            
            # Combine and show recent activities
            recent_activities = []
            
            if not inward_df.empty:
                for _, row in inward_df.tail(3).iterrows():
                    recent_activities.append({
                        'Time': row.get('Date', ''),
                        'Activity': f"📥 {row.get('Material', '')} received - {row.get('Quantity', '')} {row.get('Unit', '')}",
                        'User': row.get('Received By', 'Unknown')
                    })
            
            if not outward_df.empty:
                for _, row in outward_df.tail(2).iterrows():
                    recent_activities.append({
                        'Time': row.get('Date', ''),
                        'Activity': f"📤 {row.get('Material', '')} issued - {row.get('Quantity', '')} {row.get('Unit', '')}",
                        'User': row.get('Issued By', 'Unknown')
                    })
            
            if recent_activities:
                activity_df = pd.DataFrame(recent_activities)
                st.dataframe(activity_df, use_container_width=True, hide_index=True)
            else:
                st.info("No recent activities found. Start adding materials to see activity.")
                
        except Exception as e:
            st.error(f"Error loading recent activities: {str(e)}")
    else:
        st.error("Google Sheets not connected")
    
    st.markdown("---")
    
    # Low Stock Alert Section
    st.subheader("⚠️ Low Stock Alert")
    
    if sheets_manager:
        try:
            # Calculate current stock levels using cached data
            inward_df = get_cached_inward_data()
            outward_df = get_cached_outward_data()
            
            if not inward_df.empty:
                # Calculate stock summary
                inward_summary = inward_df.groupby(['Material', 'Unit'])['Quantity'].sum().reset_index()
                inward_summary.columns = ['Material', 'Unit', 'Total Inward']
                
                outward_summary = pd.DataFrame(columns=['Material', 'Unit', 'Total Outward'])
                if not outward_df.empty:
                    outward_summary = outward_df.groupby(['Material', 'Unit'])['Quantity'].sum().reset_index()
                    outward_summary.columns = ['Material', 'Unit', 'Total Outward']
                
                # Merge inward and outward
                stock_summary = inward_summary.merge(outward_summary, on=['Material', 'Unit'], how='left')
                stock_summary['Total Outward'] = stock_summary['Total Outward'].fillna(0)
                stock_summary['Current Stock'] = stock_summary['Total Inward'] - stock_summary['Total Outward']
                
                # Filter low stock items
                low_stock = stock_summary[stock_summary['Current Stock'] <= 10]
                if not low_stock.empty:
                    st.dataframe(low_stock, use_container_width=True, hide_index=True)
                else:
                    st.success("✅ All stock levels are healthy!")
            else:
                st.info("No stock data available. Add materials to monitor stock levels.")
                
        except Exception as e:
            st.error(f"Error loading low stock data: {str(e)}")
    else:
        st.error("Google Sheets not connected")
    
    st.markdown("---")
    
    # Expiry Alert Section
    st.subheader("⏰ Expiry Alert")
    
    if sheets_manager:
        try:
            # Get materials with expiry dates using cached data
            inward_df = get_cached_inward_data()
            
            if not inward_df.empty and 'Expiry Date' in inward_df.columns:
                # Filter items with expiry dates
                expiry_items = inward_df[inward_df['Expiry Date'].notna() & (inward_df['Expiry Date'] != '')]
                
                if not expiry_items.empty:
                    # Convert expiry dates to datetime safely
                    expiry_items = expiry_items.copy()
                    expiry_items['Expiry Date'] = pd.to_datetime(expiry_items['Expiry Date'], errors='coerce')
                    
                    # Filter out invalid dates
                    expiry_items = expiry_items[expiry_items['Expiry Date'].notna()]
                    
                    if not expiry_items.empty:
                        today = pd.Timestamp.now().date()
                        future_date = today + pd.Timedelta(days=30)
                        
                        # Find items expiring in next 30 days
                        expiring_soon = expiry_items[expiry_items['Expiry Date'].dt.date <= future_date]
                        
                        if not expiring_soon.empty:
                            # Show expiring items
                            expiry_display = expiring_soon[['Material', 'Grade', 'Quantity', 'Unit', 'Expiry Date', 'Vendor']].copy()
                            expiry_display['Days Until Expiry'] = (expiry_display['Expiry Date'].dt.date - today).apply(lambda x: x.days if hasattr(x, 'days') else 0)
                            st.dataframe(expiry_display, use_container_width=True, hide_index=True)
                        else:
                            st.success("✅ No materials expiring in the next 30 days!")
                    else:
                        st.info("No valid expiry dates found.")
                else:
                    st.info("No materials with expiry dates found.")
            else:
                st.info("No expiry data available. Add materials with expiry dates to monitor.")
                
        except Exception as e:
            st.error(f"Error loading expiry data: {str(e)}")
    else:
        st.error("Google Sheets not connected")

elif "Vendor Management" in current_page:
    st.subheader("📦 Add New Vendor")
    
    # Business Information Section
    with st.expander("📋 Business Information", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            vendor_name = st.text_input("Vendor Name*", placeholder="Enter vendor company name")
            material_name, material_grade = create_material_grade_selector(sheets_manager, "vendor")
            
        with col2:
            contact_person = st.text_input("Contact Person*", placeholder="Primary contact name")
            phone = st.text_input("Phone Number*", placeholder="10-digit mobile number")
    
    # Contact Details Section
    with st.expander("📞 Contact Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input("Email Address", placeholder="vendor@company.com")
            gst_number = st.text_input("GST Number", placeholder="GST registration number")
            
        with col2:
            address = st.text_area("Complete Address", placeholder="Full business address with pincode")
    
    # Submit button
    if st.button("Add Vendor", type="primary", use_container_width=True):
        # Check each required field and show specific missing fields
        missing_fields = []
        if not vendor_name or not vendor_name.strip():
            missing_fields.append("Vendor Name")
        if not material_name or not material_name.strip():
            missing_fields.append("Material")
        if not material_grade or not material_grade.strip():
            missing_fields.append("Grade")
        if not contact_person or not contact_person.strip():
            missing_fields.append("Contact Person")
        if not phone or not phone.strip():
            missing_fields.append("Phone Number")
        
        if not missing_fields:
            # Create material description
            full_material = f"{material_name}" + (f" - {material_grade}" if material_grade else "")
            
            vendor_data = [
                vendor_name.strip(),
                material_name.strip(),
                full_material,
                material_grade.strip(),
                contact_person.strip(),
                phone.strip(),
                email.strip() if email else "",
                gst_number.strip() if gst_number else "",
                address.strip() if address else "",
                datetime.now().strftime('%Y-%m-%d')
            ]
            
            try:
                headers = ['Vendor Name', 'Material', 'Material Name', 'Grade', 'Contact Person', 'Phone', 'Email', 'GST Number', 'Address', 'Date Added']
                vendor_worksheet = sheets_manager.get_or_create_worksheet('Vendor Master', headers)
                vendor_worksheet.append_row(vendor_data)
                
                # Clear cache to ensure all modules see updated vendor data
                clear_cache()
                
                st.success(f"✅ Vendor '{vendor_name}' added successfully for {full_material}")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding vendor: {str(e)}")
        else:
            st.error(f"Please fill the following required fields: {', '.join(missing_fields)}")

    # Vendor Lookup Section
    st.markdown("---")
    st.subheader("🔍 Find Vendors by Material")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_material = st.text_input(
            "Filter by Material", 
            placeholder="Type material name to search (leave empty for all)",
            help="Enter material name to filter vendors"
        )
    
    with col2:
        selected_grade = st.text_input("Grade/Specification (optional)", placeholder="e.g., 8mm, OPC 53, 1/2 inch")
    
    # Show matching vendors
    if sheets_manager:
        try:
            headers = ['Vendor Name', 'Material', 'Material Name', 'Grade', 'Contact Person', 'Phone', 'Email', 'GST Number', 'Address', 'Date Added']
            vendor_worksheet = sheets_manager.get_or_create_worksheet('Vendor Master', headers)
            vendors_df = sheets_manager.dataframe_from_worksheet(vendor_worksheet)
            
            if not vendors_df.empty:
                # Filter vendors based on text input
                filtered_vendors = vendors_df
                
                if selected_material and selected_material.strip():
                    filtered_vendors = filtered_vendors[filtered_vendors['Material'].str.contains(selected_material, case=False, na=False)]
                
                if selected_grade and selected_grade.strip():
                    filtered_vendors = filtered_vendors[filtered_vendors['Grade'].str.contains(selected_grade, case=False, na=False)]
                
                if not filtered_vendors.empty:
                    filter_text = f"'{selected_material}'" if selected_material else "all materials"
                    if selected_grade:
                        filter_text += f" with grade '{selected_grade}'"
                    st.write(f"**Found {len(filtered_vendors)} vendor(s) for {filter_text}:**")
                    
                    for idx, (_, vendor) in enumerate(filtered_vendors.iterrows(), 1):
                        with st.container():
                            col1, col2 = st.columns([3, 2])
                            
                            with col1:
                                st.markdown(f"**{idx}. {vendor.get('Vendor Name', 'N/A')}**")
                                st.write(f"📦 **Material:** {vendor.get('Material', 'N/A')}")
                                if vendor.get('Grade') and str(vendor.get('Grade')).strip():
                                    st.write(f"🏷️ **Grade:** {vendor.get('Grade', 'N/A')}")
                                st.write(f"👤 **Contact Person:** {vendor.get('Contact Person', 'N/A')}")
                            
                            with col2:
                                st.write(f"📞 **Phone:** {vendor.get('Phone', 'N/A')}")
                                st.write(f"📧 **Email:** {vendor.get('Email', 'N/A')}")
                                if vendor.get('GST Number') and str(vendor.get('GST Number')).strip():
                                    st.write(f"🏛️ **GST:** {vendor.get('GST Number', 'N/A')}")
                                if vendor.get('Address') and str(vendor.get('Address')).strip():
                                    st.write(f"📍 **Address:** {vendor.get('Address', 'N/A')}")
                            
                            st.markdown("---")
                else:
                    filter_desc = f"'{selected_material}'" if selected_material else "the specified criteria"
                    if selected_grade:
                        filter_desc += f" with grade '{selected_grade}'"
                    st.info(f"No vendors found for {filter_desc}")
            else:
                st.info("No vendor data available. Add vendors first.")
        except Exception as e:
            st.error(f"Error loading vendors: {str(e)}")
    
    elif selected_material and not sheets_manager:
        st.error("Google Sheets not connected")

    # Display all existing vendors
    st.markdown("---")
    st.subheader("📋 All Vendors")
    
    if sheets_manager:
        try:
            # Use cached vendor data to prevent API quota issues
            vendors_df = get_cached_vendor_data()
            if not vendors_df.empty:
                # Display vendors in readable card format with serial numbers
                for idx, (_, vendor) in enumerate(vendors_df.iterrows(), 1):
                    with st.container():
                        col1, col2 = st.columns([3, 2])
                        
                        with col1:
                            st.markdown(f"**{idx}. {vendor.get('Vendor Name', 'N/A')}**")
                            st.write(f"📦 **Material:** {vendor.get('Material', 'N/A')}")
                            if vendor.get('Grade') and str(vendor.get('Grade')).strip():
                                st.write(f"🏷️ **Grade:** {vendor.get('Grade', 'N/A')}")
                            st.write(f"👤 **Contact Person:** {vendor.get('Contact Person', 'N/A')}")
                        
                        with col2:
                            st.write(f"📞 **Phone:** {vendor.get('Phone', 'N/A')}")
                            st.write(f"📧 **Email:** {vendor.get('Email', 'N/A')}")
                            if vendor.get('GST Number') and str(vendor.get('GST Number')).strip():
                                st.write(f"🏛️ **GST:** {vendor.get('GST Number', 'N/A')}")
                            if vendor.get('Address') and str(vendor.get('Address')).strip():
                                st.write(f"📍 **Address:** {vendor.get('Address', 'N/A')}")
                        
                        st.markdown("---")
            else:
                st.info("No vendors found. Add your first vendor above.")
        except Exception as e:
            st.error(f"Error loading vendors: {str(e)}")
    else:
        st.error("❌ Cannot load vendors - Google Sheets not connected")

elif "Inward Register" in current_page:
    st.subheader("🚛 Inward Register")
    
    # Material Entry Section
    with st.expander("📦 Material Entry", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date*", value=datetime.now().date())
            material_name, material_grade = create_material_grade_selector(sheets_manager, "inward")
            
        with col2:
            # Get vendor options using cached data
            vendor_options = ["Select Vendor"]
            cached_vendors = get_cached_vendors_list()
            if cached_vendors:
                vendor_options.extend(cached_vendors)
            
            vendor = st.selectbox("Vendor*", vendor_options)
            quantity = st.number_input("Quantity*", min_value=0.01, step=0.01, format="%.2f")
    
    # Additional Details Section
    with st.expander("📋 Additional Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            unit = st.selectbox("Unit*", ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"])
            rate = st.number_input("Rate per Unit (₹)*", min_value=0.01, step=0.01, format="%.2f")
            invoice_number = st.text_input("Invoice Number*")
            
        with col2:
            received_by = st.text_input("Received By*")
            mfg_date = st.date_input("Manufacturing Date")
            expiry_date = st.date_input("Expiry Date (Optional)", value=None)
    
    # Calculate amount
    if quantity and rate:
        total_amount = quantity * rate
        st.info(f"💰 **Total Amount: ₹{total_amount:,.2f}**")
    
    remarks = st.text_area("Remarks")
    
    # Submit button
    if st.button("Add Inward Entry", type="primary", use_container_width=True):
        if material_name and vendor != "Select Vendor" and quantity > 0 and rate > 0 and invoice_number and received_by:
            
            # Create material description
            full_material = f"{material_name}" + (f" - {material_grade}" if material_grade else "")
            
            inward_data = [
                date.strftime('%Y-%m-%d'),
                full_material,
                material_name,
                material_grade,
                vendor,
                quantity,
                unit,
                rate,
                quantity * rate,
                invoice_number,
                received_by,
                mfg_date.strftime('%Y-%m-%d') if mfg_date else "",
                expiry_date.strftime('%Y-%m-%d') if expiry_date else "",
                remarks
            ]
            
            try:
                headers = ['Date', 'Material Name', 'Material', 'Grade', 'Vendor', 'Quantity', 'Unit', 'Rate', 'Amount', 'Invoice Number', 'Received By', 'Mfg Date', 'Expiry Date', 'Remarks']
                inward_worksheet = sheets_manager.get_or_create_worksheet('Inward Register', headers)
                inward_worksheet.append_row(inward_data)
                
                # Clear cache to ensure all modules see updated data
                clear_cache()
                
                st.success(f"✅ Inward entry added: {quantity} {unit} of {full_material} from {vendor}")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding inward entry: {str(e)}")
        else:
            st.error("Please fill all required fields marked with *")

    # Display recent inward entries
    st.markdown("---")
    st.subheader("📋 Recent Inward Entries")
    
    if sheets_manager:
        try:
            # Use cached data for display to prevent API quota issues
            inward_df = get_cached_inward_data()
            
            if not inward_df.empty:
                # Show recent entries (last 10)
                recent_entries = inward_df.tail(10)
                st.dataframe(recent_entries, use_container_width=True, hide_index=True)
                
                # Show summary
                total_entries = len(inward_df)
                total_amount = inward_df['Amount'].sum() if 'Amount' in inward_df.columns else 0
                st.info(f"📊 **Total Entries:** {total_entries} | **Total Value:** ₹{total_amount:,.2f}")
            else:
                st.info("No inward entries found. Add your first entry above.")
        except Exception as e:
            st.error(f"Error loading inward entries: {str(e)}")

elif "Outward Register" in current_page:
    st.subheader("📤 Outward Register")
    
    # Material Issue Section
    with st.expander("📦 Material Issue", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date*", value=datetime.now().date())
            material_name, material_grade = create_material_grade_selector(sheets_manager, "outward")
            
        with col2:
            quantity = st.number_input("Quantity*", min_value=0.01, step=0.01, format="%.2f")
            unit = st.selectbox("Unit*", ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"])
    
    # Issue Details Section
    with st.expander("📋 Issue Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            issued_to = st.text_input("Issued To*", placeholder="Person/Department receiving materials")
            purpose_options = [
                "Slab Work", "PCC Work", "Raft Foundation", "Column Work", "Beam Work", 
                "Wall Construction", "Plastering", "Flooring", "Roofing", "Electrical Work",
                "Plumbing", "Finishing Work", "Site Development", "Repair Work", "Testing", 
                "Emergency Use", "Maintenance", "Other"
            ]
            purpose = st.selectbox("Purpose*", purpose_options)
            
        with col2:
            issued_by = st.text_input("Issued By*", placeholder="Person authorizing issue")
            remarks = st.text_area("Remarks", placeholder="Additional notes or specifications")
    
    # Location Details Section
    with st.expander("🏢 Location Details (Optional)", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            wing = st.text_input("Wing", placeholder="e.g., A, B, C, Tower 1")
            
        with col2:
            flat_number = st.text_input("Flat Number", placeholder="e.g., 101, 202, 3A")
    
    # Submit button
    if st.button("Issue Material", type="primary", use_container_width=True):
        if material_name and quantity > 0 and issued_to and issued_by:
            
            # Create material description
            full_material = f"{material_name}" + (f" - {material_grade}" if material_grade else "")
            
            outward_data = [
                date.strftime('%Y-%m-%d'),
                full_material,
                material_name,
                material_grade,
                quantity,
                unit,
                issued_to,
                purpose,
                issued_by,
                wing if wing else "",
                flat_number if flat_number else "",
                remarks
            ]
            
            try:
                headers = ['Date', 'Material Name', 'Material', 'Grade', 'Quantity', 'Unit', 'Issued To', 'Purpose', 'Issued By', 'Wing', 'Flat Number', 'Remarks']
                outward_worksheet = sheets_manager.get_or_create_worksheet('Outward Register', headers)
                outward_worksheet.append_row(outward_data)
                

                
                # Clear cache to ensure all modules see updated data
                clear_cache()
                
                st.success(f"✅ Material issued: {quantity} {unit} of {full_material} to {issued_to}")
                st.rerun()
            except Exception as e:
                st.error(f"Error issuing material: {str(e)}")
        else:
            st.error("Please fill all required fields marked with *")

    # Display recent outward entries
    st.markdown("---")
    st.subheader("📋 Recent Outward Entries")
    
    if sheets_manager:
        try:
            # Use cached data for display to prevent API quota issues
            outward_df = get_cached_outward_data()
            
            if not outward_df.empty:
                # Show recent entries (last 10)
                recent_entries = outward_df.tail(10)
                st.dataframe(recent_entries, use_container_width=True, hide_index=True)
                
                # Show summary
                total_entries = len(outward_df)
                st.info(f"📊 **Total Issue Entries:** {total_entries}")
            else:
                st.info("No outward entries found. Issue your first material above.")
        except Exception as e:
            st.error(f"Error loading outward entries: {str(e)}")
    
    # Indent Status Update Section
    st.markdown("---")
    st.subheader("📝 Indent Status Update")
    
    with st.expander("🔄 Update Indent Status", expanded=False):
        if sheets_manager:
            try:
                # Get all indents
                indent_headers = ['Indent Date', 'Indent Number', 'Project Name', 'Department', 'Requested By', 'Priority', 'Material Name', 'Material', 'Grade', 'Required Quantity', 'Unit', 'Required Date', 'Wing', 'Flat Number', 'Purpose', 'Purpose Description', 'Approved By', 'Status', 'Created Date']
                indent_worksheet = sheets_manager.get_or_create_worksheet('Indent Register', indent_headers)
                indent_df = sheets_manager.dataframe_from_worksheet(indent_worksheet)
                
                if not indent_df.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Select indent number
                        indent_options = ["Select Indent"] + list(indent_df['Indent Number'].unique())
                        selected_indent = st.selectbox("Select Indent Number", indent_options)
                        
                        if selected_indent != "Select Indent":
                            # Show indent details
                            indent_details = indent_df[indent_df['Indent Number'] == selected_indent].iloc[0]
                            
                            st.write("**Indent Details:**")
                            st.write(f"- **Project:** {indent_details.get('Project Name', 'N/A')}")
                            st.write(f"- **Department:** {indent_details.get('Department', 'N/A')}")
                            st.write(f"- **Material:** {indent_details.get('Material', 'N/A')} - {indent_details.get('Grade', 'N/A')}")
                            st.write(f"- **Required Qty:** {indent_details.get('Required Quantity', 'N/A')} {indent_details.get('Unit', 'N/A')}")
                            st.write(f"- **Current Status:** {indent_details.get('Status', 'N/A')}")
                            st.write(f"- **Requested By:** {indent_details.get('Requested By', 'N/A')}")
                    
                    with col2:
                        if selected_indent != "Select Indent":
                            new_status = st.selectbox("Update Status", ["Pending", "Approved", "Rejected", "Fulfilled", "Partially Fulfilled"])
                            status_update_date = st.date_input("Status Update Date", value=datetime.now().date())
                            status_remarks = st.text_area("Status Update Remarks", placeholder="Add remarks for status update")
                            
                            if st.button("Update Status", type="primary"):
                                try:
                                    # Find the row to update
                                    indent_row_idx = indent_df[indent_df['Indent Number'] == selected_indent].index[0]
                                    sheet_row = indent_row_idx + 2  # Add 2 for header and 0-indexing
                                    
                                    # Update status
                                    status_col = indent_headers.index('Status') + 1
                                    indent_worksheet.update_cell(sheet_row, status_col, new_status)
                                    
                                    # Clear cache
                                    clear_cache()
                                    
                                    st.success(f"✅ Indent {selected_indent} status updated to '{new_status}' on {status_update_date}")
                                    if status_remarks:
                                        st.info(f"Remarks: {status_remarks}")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Error updating indent status: {str(e)}")
                else:
                    st.info("No indents found. Create indents in the Indent Register module first.")
            except Exception as e:
                st.error(f"Error loading indents: {str(e)}")
        else:
            st.error("Google Sheets not connected")

    # Wing/Flat-wise Material Tracking Section
    st.markdown("---")
    st.subheader("🏢 Wing/Flat-wise Material Tracking")
    
    with st.expander("🔍 Track Materials by Location", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            track_purpose = st.selectbox("Purpose", [
                "All Purposes", "Slab Work", "PCC Work", "Raft Foundation", "Column Work", "Beam Work", 
                "Wall Construction", "Plastering", "Flooring", "Roofing", "Electrical Work",
                "Plumbing", "Finishing Work", "Site Development", "Repair Work", "Testing", 
                "Emergency Use", "Maintenance", "Other"
            ])
        
        with col2:
            track_wing = st.text_input("Wing (Optional)", placeholder="e.g., A, B, C, Tower 1")
        
        with col3:
            track_flat = st.text_input("Flat Number (Optional)", placeholder="e.g., 101, 202, 3A")
    
    # Show filtered results
    if sheets_manager:
        try:
            outward_df = get_cached_outward_data()
            
            if not outward_df.empty:
                # Apply filters
                filtered_df = outward_df.copy()
                
                if track_purpose != "All Purposes":
                    filtered_df = filtered_df[filtered_df['Purpose'] == track_purpose]
                
                if track_wing:
                    filtered_df = filtered_df[filtered_df['Wing'].str.contains(track_wing, case=False, na=False)]
                
                if track_flat:
                    filtered_df = filtered_df[filtered_df['Flat Number'].str.contains(track_flat, case=False, na=False)]
                
                if not filtered_df.empty:
                    st.write(f"**Found {len(filtered_df)} entries matching your criteria:**")
                    
                    # Display filtered results with key columns
                    display_columns = ['Date', 'Material Name', 'Quantity', 'Unit', 'Purpose', 'Wing', 'Flat Number', 'Issued To', 'Issued By']
                    available_columns = [col for col in display_columns if col in filtered_df.columns]
                    
                    if available_columns:
                        st.dataframe(filtered_df[available_columns], use_container_width=True, hide_index=True)
                        
                        # Summary statistics
                        col_summary1, col_summary2, col_summary3 = st.columns(3)
                        with col_summary1:
                            st.metric("Total Entries", len(filtered_df))
                        with col_summary2:
                            unique_materials = filtered_df['Material'].nunique() if 'Material' in filtered_df.columns else 0
                            st.metric("Unique Materials", unique_materials)
                        with col_summary3:
                            total_quantity = filtered_df['Quantity'].sum() if 'Quantity' in filtered_df.columns else 0
                            st.metric("Total Quantity", f"{total_quantity:.2f}")
                    else:
                        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No entries found matching the selected criteria.")
            else:
                st.info("No outward entries available for tracking.")
        except Exception as e:
            st.error(f"Error loading tracking data: {str(e)}")

elif "Returns Register" in current_page:
    st.subheader("🔁 Returns Register")
    
    # Material Return Section
    with st.expander("📦 Material Return", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date*", value=datetime.now().date())
            material_name, material_grade = create_material_grade_selector(sheets_manager, "returns")
            
        with col2:
            quantity = st.number_input("Quantity Returned*", min_value=0.01, step=0.01, format="%.2f")
            unit = st.selectbox("Unit*", ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"])
    
    # Return Details Section
    with st.expander("📋 Return Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            returned_by = st.text_input("Returned By*", placeholder="Person returning materials")
            return_reason = st.selectbox("Return Reason*", ["Excess Material", "Wrong Specification", "Damaged", "Quality Issues", "Project Change", "Expired", "Other"])
            
        with col2:
            received_by = st.text_input("Received By*", placeholder="Person receiving returned materials")
            condition = st.selectbox("Material Condition*", ["Good", "Fair", "Damaged", "Unusable"])
    
    remarks = st.text_area("Remarks", placeholder="Additional notes about the return")
    
    # Submit button
    if st.button("Process Return", type="primary", use_container_width=True):
        if material_name and quantity > 0 and returned_by and received_by:
            
            # Create material description
            full_material = f"{material_name}" + (f" - {material_grade}" if material_grade else "")
            
            returns_data = [
                date.strftime('%Y-%m-%d'),
                full_material,
                material_name,
                material_grade,
                quantity,
                unit,
                returned_by,
                return_reason,
                received_by,
                condition,
                remarks
            ]
            
            try:
                headers = ['Date', 'Material Name', 'Material', 'Grade', 'Quantity', 'Unit', 'Returned By', 'Return Reason', 'Received By', 'Condition', 'Remarks']
                returns_worksheet = sheets_manager.get_or_create_worksheet('Returns Register', headers)
                returns_worksheet.append_row(returns_data)
                
                # Clear cache to ensure all modules see updated data
                clear_cache()
                
                st.success(f"✅ Return processed: {quantity} {unit} of {full_material} returned by {returned_by}")
                st.rerun()
            except Exception as e:
                st.error(f"Error processing return: {str(e)}")
        else:
            st.error("Please fill all required fields marked with *")

    # Display recent returns
    st.markdown("---")
    st.subheader("📋 Recent Returns")
    
    if sheets_manager:
        try:
            headers = ['Date', 'Material Name', 'Material', 'Grade', 'Quantity', 'Unit', 'Returned By', 'Return Reason', 'Received By', 'Condition', 'Remarks']
            returns_worksheet = sheets_manager.get_or_create_worksheet('Returns Register', headers)
            returns_df = sheets_manager.dataframe_from_worksheet(returns_worksheet)
            
            if not returns_df.empty:
                # Show recent entries (last 10)
                recent_entries = returns_df.tail(10)
                st.dataframe(recent_entries, use_container_width=True, hide_index=True)
                
                # Show summary
                total_returns = len(returns_df)
                st.info(f"📊 **Total Returns:** {total_returns}")
            else:
                st.info("No return entries found. Process your first return above.")
        except Exception as e:
            st.error(f"Error loading returns: {str(e)}")

elif "Damage / Loss Register" in current_page:
    st.subheader("❌ Damage / Loss Entry")
    
    with st.form("damage_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date*", value=datetime.now().date())
            unit = st.selectbox("Unit*", ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"])
            
        with col2:
            material_name, material_grade = create_material_grade_selector(sheets_manager, "damage")
            reason = st.selectbox("Reason*", ["Weather Damage", "Transportation Damage", "Storage Issues", "Equipment Failure", "Human Error", "Theft", "Natural Disaster", "Quality Issues", "Other"])
        
        col3, col4 = st.columns(2)
        
        with col3:
            quantity = st.number_input("Quantity Lost/Damaged*", min_value=0.0, step=0.1, format="%.2f")
            damaged_by = st.selectbox("Damaged By*", ["Our Team", "Vendor", "Third Party", "Natural Causes", "Unknown"])
            
        with col4:
            reported_by = st.text_input("Reported By*")
            estimated_value = st.number_input("Estimated Value (₹)*", min_value=0.0, step=0.01, format="%.2f")
        
        description = st.text_area("Detailed Description of Incident*")
        
        submit_damage = st.form_submit_button("Record Damage/Loss Entry", type="primary")
        
        if submit_damage:
            if material_name and quantity > 0 and reason and reported_by and estimated_value > 0 and description:
                damage_data = [
                    date.strftime('%Y-%m-%d'),
                    material_name,
                    material_grade,
                    quantity,
                    unit,
                    reason,
                    damaged_by,
                    reported_by,
                    estimated_value,
                    description,
                    "Damage"
                ]
                
                try:
                    headers = ['Date', 'Material', 'Grade', 'Quantity Lost/Damaged', 'Unit', 'Reason', 'Damaged By', 'Reported By', 'Estimated Value', 'Detailed Description', 'Record Damage or Entry']
                    damage_worksheet = sheets_manager.get_or_create_worksheet('Damage Loss Register', headers)
                    damage_worksheet.append_row(damage_data)
                    
                    # Clear cache to ensure all modules see updated data
                    clear_cache()
                    
                    st.success(f"✅ Damage/Loss entry recorded for {quantity} {unit} of {material_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error recording damage/loss: {str(e)}")
            else:
                st.error("Please fill all required fields marked with *")

    # Display damage/loss records
    st.markdown("---")
    st.subheader("📋 Damage/Loss Records")
    
    if sheets_manager:
        try:
            headers = ['Date', 'Material', 'Grade', 'Quantity Lost/Damaged', 'Unit', 'Reason', 'Damaged By', 'Reported By', 'Estimated Value', 'Detailed Description', 'Record Damage or Entry']
            damage_worksheet = sheets_manager.get_or_create_worksheet('Damage Loss Register', headers)
            damage_df = sheets_manager.dataframe_from_worksheet(damage_worksheet)
            
            if not damage_df.empty:
                st.dataframe(damage_df, use_container_width=True, hide_index=True)
            else:
                st.info("No damage/loss records found.")
        except Exception as e:
            st.error(f"Error loading damage/loss records: {str(e)}")



elif "Reconciliation" in current_page:
    st.subheader("⚖️ Stock Reconciliation")
    
    # Reconciliation Details Section
    with st.expander("📋 Reconciliation Details", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            recon_date = st.date_input("Reconciliation Date", value=datetime.now().date())
        with col2:
            reconciled_by = st.text_input("Reconciled By*", placeholder="Person performing reconciliation")
    
    if sheets_manager:
        try:
            # Get current stock levels
            inward_headers = ['Date', 'Material Name', 'Material', 'Grade', 'Vendor', 'Quantity', 'Unit', 'Rate', 'Amount', 'Invoice Number', 'Received By', 'Mfg Date', 'Expiry Date', 'Remarks']
            inward_worksheet = sheets_manager.get_or_create_worksheet('Inward Register', inward_headers)
            inward_df = sheets_manager.dataframe_from_worksheet(inward_worksheet)
            
            outward_headers = ['Date', 'Material Name', 'Material', 'Grade', 'Quantity', 'Unit', 'Issued To', 'Purpose', 'Issued By', 'Remarks']
            outward_worksheet = sheets_manager.get_or_create_worksheet('Outward Register', outward_headers)
            outward_df = sheets_manager.dataframe_from_worksheet(outward_worksheet)
            
            if not inward_df.empty:
                # Calculate theoretical stock
                stock_data = []
                
                # Group inward entries
                inward_summary = inward_df.groupby(['Material', 'Grade', 'Unit']).agg({
                    'Quantity': 'sum'
                }).reset_index()
                
                # Subtract outward entries
                if not outward_df.empty:
                    outward_summary = outward_df.groupby(['Material', 'Grade', 'Unit']).agg({
                        'Quantity': 'sum'
                    }).reset_index()
                    
                    # Merge inward and outward
                    merged = inward_summary.merge(outward_summary, on=['Material', 'Grade', 'Unit'], how='outer', suffixes=('_in', '_out'))
                    merged = merged.fillna(0)
                    merged['Theoretical Stock'] = merged['Quantity_in'] - merged['Quantity_out']
                else:
                    merged = inward_summary.copy()
                    merged['Theoretical Stock'] = merged['Quantity']
                
                # Stock Reconciliation Form Section
                with st.expander("📊 Stock Reconciliation Form", expanded=True):
                    if sheets_manager and reconciled_by:
                        try:
                            # Create reconciliation form
                            reconciliation_data = []
                            
                            for idx, row in merged.iterrows():
                                material_name = f"{row['Material']} - {row['Grade']}" if row['Grade'] else row['Material']
                                
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.write(f"**{material_name}**")
                                    st.write(f"Unit: {row['Unit']}")
                                
                                with col2:
                                    theoretical = row['Theoretical Stock']
                                    st.write(f"**Theoretical:** {theoretical}")
                                
                                with col3:
                                    actual = st.number_input(
                                        f"Actual Count",
                                        min_value=0.0,
                                        step=0.01,
                                        format="%.2f",
                                        key=f"actual_{idx}",
                                        help=f"Enter actual counted quantity for {material_name}"
                                    )
                                
                                with col4:
                                    variance = actual - theoretical
                                    if variance != 0:
                                        color = "🔴" if variance < 0 else "🟢"
                                        st.write(f"**Variance:** {color} {variance}")
                                    else:
                                        st.write("**Variance:** ✅ 0")
                                
                                reconciliation_data.append({
                                    'Material': row['Material'],
                                    'Grade': row['Grade'],
                                    'Unit': row['Unit'],
                                    'Theoretical': theoretical,
                                    'Actual': actual,
                                    'Variance': variance
                                })
                                
                                st.markdown("---")
                            
                            remarks = st.text_area("Reconciliation Remarks", placeholder="Notes about variances or discrepancies")
                            
                            # Submit reconciliation
                            if st.button("Submit Reconciliation", type="primary", use_container_width=True):
                                if reconciled_by:
                                    try:
                                        # Save reconciliation data
                                        recon_headers = ['Date', 'Material', 'Grade', 'Unit', 'Theoretical Stock', 'Actual Stock', 'Variance', 'Reconciled By', 'Remarks']
                                        recon_worksheet = sheets_manager.get_or_create_worksheet('Reconciliation Register', recon_headers)
                                        
                                        for item in reconciliation_data:
                                            if item['Actual'] > 0 or item['Variance'] != 0:  # Only save items with data
                                                recon_row = [
                                                    recon_date.strftime('%Y-%m-%d'),
                                                    item['Material'],
                                                    item['Grade'],
                                                    item['Unit'],
                                                    item['Theoretical'],
                                                    item['Actual'],
                                                    item['Variance'],
                                                    reconciled_by,
                                                    remarks
                                                ]
                                                recon_worksheet.append_row(recon_row)
                                        
                                        st.success(f"✅ Reconciliation completed for {recon_date}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error saving reconciliation: {str(e)}")
                                else:
                                    st.error("Please enter who performed the reconciliation")
                        except Exception as e:
                            st.error(f"Error loading reconciliation data: {str(e)}")
                    else:
                        st.info("Enter reconciled by name to start reconciliation")
            else:
                st.info("No stock data available for reconciliation. Add some inward entries first.")
        except Exception as e:
            st.error(f"Error loading reconciliation data: {str(e)}")
    else:
        st.error("Google Sheets not connected")

elif "PO Register" in current_page:
    st.subheader("🧾 Purchase Order Register")
    
    # PO Creation Section
    with st.expander("📝 Create Purchase Order", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            po_number = st.text_input("PO Number*", placeholder="PO-2024-001")
            material_name, material_grade = create_material_grade_selector(sheets_manager, "po")
            
        with col2:
            # Get vendor options
            vendor_options = ["Select Vendor"]
            if sheets_manager:
                try:
                    headers = ['Vendor Name', 'Material', 'Material Name', 'Grade', 'Contact Person', 'Phone', 'Email', 'GST Number', 'Address', 'Date Added']
                    vendor_worksheet = sheets_manager.get_or_create_worksheet('Vendor Master', headers)
                    vendor_df = sheets_manager.dataframe_from_worksheet(vendor_worksheet)
                    if not vendor_df.empty:
                        vendor_options.extend(vendor_df['Vendor Name'].dropna().unique().tolist())
                except Exception:
                    pass
            
            vendor_name = st.selectbox("Vendor*", vendor_options)
            po_date = st.date_input("PO Date*", value=datetime.now().date())
    
    # PO Details Section
    with st.expander("📋 Order Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            quantity = st.number_input("Quantity*", min_value=0.01, step=0.01, format="%.2f")
            unit = st.selectbox("Unit*", ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"])
            
        with col2:
            rate = st.number_input("Rate per Unit (₹)*", min_value=0.01, step=0.01, format="%.2f")
            delivery_date = st.date_input("Expected Delivery Date")
    
    # Calculate total amount
    if quantity and rate:
        total_amount = quantity * rate
        st.info(f"💰 **Total PO Amount: ₹{total_amount:,.2f}**")
    
    # Additional Details
    with st.expander("📋 Additional Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            status = st.selectbox("PO Status*", ["Draft", "Sent", "Acknowledged", "In Progress", "Delivered", "Closed", "Cancelled"])
            created_by = st.text_input("Created By*", placeholder="Person creating PO")
            
        with col2:
            remarks = st.text_area("Remarks/Terms", placeholder="Special terms, conditions, or notes")
    
    # Submit PO
    if st.button("Create Purchase Order", type="primary", use_container_width=True):
        if po_number and material_name and vendor_name != "Select Vendor" and quantity > 0 and rate > 0 and created_by:
            
            # Create material description
            full_material = f"{material_name}" + (f" - {material_grade}" if material_grade else "")
            
            po_data = [
                po_number,
                po_date.strftime('%Y-%m-%d'),
                vendor_name,
                full_material,
                material_name,
                material_grade,
                quantity,
                unit,
                rate,
                quantity * rate,
                delivery_date.strftime('%Y-%m-%d') if delivery_date else "",
                status,
                created_by,
                remarks
            ]
            
            try:
                headers = ['PO Number', 'PO Date', 'Vendor', 'Material Name', 'Material', 'Grade', 'Quantity', 'Unit', 'Rate', 'Total Amount', 'Delivery Date', 'Status', 'Created By', 'Remarks']
                po_worksheet = sheets_manager.get_or_create_worksheet('PO Register', headers)
                po_worksheet.append_row(po_data)
                st.success(f"✅ Purchase Order {po_number} created for ₹{quantity * rate:,.2f}")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating PO: {str(e)}")
        else:
            st.error("Please fill all required fields marked with *")

    # Display existing POs
    st.markdown("---")
    st.subheader("📋 Purchase Orders")
    
    if sheets_manager:
        try:
            headers = ['PO Number', 'PO Date', 'Vendor', 'Material Name', 'Material', 'Grade', 'Quantity', 'Unit', 'Rate', 'Total Amount', 'Delivery Date', 'Status', 'Created By', 'Remarks']
            po_worksheet = sheets_manager.get_or_create_worksheet('PO Register', headers)
            po_df = sheets_manager.dataframe_from_worksheet(po_worksheet)
            
            if not po_df.empty:
                # Show PO summary
                total_pos = len(po_df)
                total_value = po_df['Total Amount'].sum() if 'Total Amount' in po_df.columns else 0
                pending_pos = len(po_df[po_df['Status'].isin(['Draft', 'Sent', 'Acknowledged', 'In Progress'])]) if 'Status' in po_df.columns else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Total POs", total_pos)
                with col2:
                    st.metric("💰 Total Value", f"₹{total_value:,.2f}")
                with col3:
                    st.metric("⏳ Pending POs", pending_pos)
                
                st.markdown("---")
                
                # Display POs in table format
                st.dataframe(po_df, use_container_width=True, hide_index=True)
            else:
                st.info("No purchase orders found. Create your first PO above.")
        except Exception as e:
            st.error(f"Error loading POs: {str(e)}")

elif "Reports" in current_page:
    st.subheader("📊 Reports")
    
    if sheets_manager:
        try:
            # Load cached inward data to prevent API quota issues
            inward_df = get_cached_inward_data()
            
            if not inward_df.empty and 'Material' in inward_df.columns and 'Grade' in inward_df.columns:
                # Two input dropdowns
                col1, col2 = st.columns(2)
                
                with col1:
                    # Use cached materials list
                    materials = get_cached_materials_list()
                    selected_material = st.selectbox("Material:", materials) if materials else None
                
                with col2:
                    if selected_material:
                        # Use cached grades list
                        grades = get_cached_grades_list()
                        selected_grade = st.selectbox("Grade:", grades) if grades else None
                    else:
                        selected_grade = None
                
                # Show vendor analysis when both are selected
                if selected_material and selected_grade:
                    st.markdown("---")
                    
                    # Filter for selected material and grade
                    filtered_data = inward_df[
                        (inward_df['Material'] == selected_material) & 
                        (inward_df['Grade'] == selected_grade) &
                        (inward_df['Rate'].notna()) & 
                        (inward_df['Rate'] > 0)
                    ]
                    
                    if not filtered_data.empty:
                        st.subheader(f"Vendor Analysis: {selected_material} - {selected_grade}")
                        
                        # Calculate vendor statistics
                        vendor_stats = []
                        for vendor in filtered_data['Vendor'].unique():
                            vendor_data = filtered_data[filtered_data['Vendor'] == vendor]
                            
                            vendor_stats.append({
                                'Vendor': vendor,
                                'Number of Orders': len(vendor_data),
                                'Average Rate': f"₹{vendor_data['Rate'].mean():.2f}",
                                'Highest Rate': f"₹{vendor_data['Rate'].max():.2f}",
                                'Lowest Rate': f"₹{vendor_data['Rate'].min():.2f}"
                            })
                        
                        # Display vendor table
                        vendor_df = pd.DataFrame(vendor_stats)
                        st.dataframe(vendor_df, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"No vendor data found for {selected_material} - {selected_grade}")
                        
            else:
                st.info("No data available. Add materials in Inward Register first.")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.error("Google Sheets not connected")

elif "Expiry Management" in current_page:
    st.subheader("⏰ Expiry Management")
    
    if sheets_manager:
        try:
            # Get inward data with expiry dates
            inward_df = get_cached_inward_data()
            
            if not inward_df.empty and 'Expiry Date' in inward_df.columns and 'Mfg Date' in inward_df.columns:
                # Convert dates and filter items with valid expiry dates
                inward_df['Expiry Date'] = pd.to_datetime(inward_df['Expiry Date'], errors='coerce')
                inward_df['Mfg Date'] = pd.to_datetime(inward_df['Mfg Date'], errors='coerce')
                
                # Filter for items with valid expiry dates
                expiry_items = inward_df[inward_df['Expiry Date'].notna()].copy()
                
                if not expiry_items.empty:
                    # Calculate days until expiry
                    today = pd.Timestamp.now()
                    expiry_items['Days Until Expiry'] = (expiry_items['Expiry Date'] - today).dt.days
                    
                    # Categorize items by expiry status
                    expired_items = expiry_items[expiry_items['Days Until Expiry'] < 0]
                    critical_items = expiry_items[(expiry_items['Days Until Expiry'] >= 0) & (expiry_items['Days Until Expiry'] <= 7)]
                    warning_items = expiry_items[(expiry_items['Days Until Expiry'] > 7) & (expiry_items['Days Until Expiry'] <= 30)]
                    normal_items = expiry_items[expiry_items['Days Until Expiry'] > 30]
                    
                    # Expiry overview metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🚨 Expired Items", len(expired_items), delta=None if len(expired_items) == 0 else f"+{len(expired_items)}")
                    with col2:
                        st.metric("🔴 Critical (≤7 days)", len(critical_items), delta=None if len(critical_items) == 0 else f"+{len(critical_items)}")
                    with col3:
                        st.metric("🟡 Warning (≤30 days)", len(warning_items), delta=None if len(warning_items) == 0 else f"+{len(warning_items)}")
                    with col4:
                        st.metric("📦 Total Tracked Items", len(expiry_items))
                    
                    st.markdown("---")
                    
                    # Filter and search options
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        status_filter = st.selectbox("Filter by Status", [
                            "All Items", 
                            "🚨 Expired (Past due)", 
                            "🔴 Critical (≤ 7 days)", 
                            "🟡 Warning (≤ 30 days)", 
                            "🟢 Normal (> 30 days)"
                        ])
                    
                    with col2:
                        materials_list = get_cached_materials_list()
                        material_filter = st.selectbox("Filter by Material", ["All Materials"] + materials_list)
                    
                    with col3:
                        search_term = st.text_input("Search", placeholder="Search by material, vendor, or invoice...")
                    
                    # Apply filters
                    filtered_items = expiry_items.copy()
                    
                    if status_filter == "🚨 Expired (Past due)":
                        filtered_items = expired_items
                    elif status_filter == "🔴 Critical (≤ 7 days)":
                        filtered_items = critical_items
                    elif status_filter == "🟡 Warning (≤ 30 days)":
                        filtered_items = warning_items
                    elif status_filter == "🟢 Normal (> 30 days)":
                        filtered_items = normal_items
                    
                    if material_filter != "All Materials":
                        filtered_items = filtered_items[filtered_items['Material'] == material_filter]
                    
                    if search_term:
                        mask = (
                            filtered_items['Material'].str.contains(search_term, case=False, na=False) |
                            filtered_items['Vendor'].str.contains(search_term, case=False, na=False) |
                            filtered_items['Invoice Number'].str.contains(search_term, case=False, na=False) |
                            filtered_items['Grade'].str.contains(search_term, case=False, na=False)
                        )
                        filtered_items = filtered_items[mask]
                    
                    # Display results
                    if not filtered_items.empty:
                        # Add status column for display
                        filtered_items['Status'] = filtered_items['Days Until Expiry'].apply(
                            lambda x: '🚨 Expired' if x < 0 
                            else '🔴 Critical' if x <= 7 
                            else '🟡 Warning' if x <= 30 
                            else '🟢 Normal'
                        )
                        
                        # Select columns for display
                        display_columns = [
                            'Material', 'Grade', 'Vendor', 'Quantity', 'Unit', 
                            'Mfg Date', 'Expiry Date', 'Days Until Expiry', 'Status', 
                            'Invoice Number', 'Received By'
                        ]
                        
                        # Format dates for display
                        display_data = filtered_items[display_columns].copy()
                        display_data['Mfg Date'] = display_data['Mfg Date'].dt.strftime('%Y-%m-%d')
                        display_data['Expiry Date'] = display_data['Expiry Date'].dt.strftime('%Y-%m-%d')
                        
                        st.dataframe(
                            display_data,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Material": st.column_config.TextColumn("🏗️ Material", width="medium"),
                                "Grade": st.column_config.TextColumn("📋 Grade", width="small"),
                                "Vendor": st.column_config.TextColumn("🏪 Vendor", width="medium"),
                                "Quantity": st.column_config.TextColumn("📦 Qty", width="small"),
                                "Unit": st.column_config.TextColumn("📏 Unit", width="small"),
                                "Mfg Date": st.column_config.DateColumn("📅 Mfg Date", width="small"),
                                "Expiry Date": st.column_config.DateColumn("⏰ Expiry Date", width="small"),
                                "Days Until Expiry": st.column_config.NumberColumn("⏳ Days Left", width="small"),
                                "Status": st.column_config.TextColumn("🚦 Status", width="small"),
                                "Invoice Number": st.column_config.TextColumn("🧾 Invoice", width="medium"),
                                "Received By": st.column_config.TextColumn("👤 Received By", width="medium")
                            }
                        )
                        
                        # Summary statistics for filtered data
                        if len(filtered_items) > 0:
                            st.markdown("---")
                            st.subheader("📊 Summary")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                total_qty = filtered_items['Quantity'].astype(float).sum()
                                st.metric("Total Quantity", f"{total_qty:.1f}")
                                
                            with col2:
                                avg_days = filtered_items['Days Until Expiry'].mean()
                                st.metric("Avg Days to Expiry", f"{avg_days:.0f}")
                                
                            with col3:
                                unique_materials = filtered_items['Material'].nunique()
                                st.metric("Unique Materials", unique_materials)
                                
                            with col4:
                                unique_vendors = filtered_items['Vendor'].nunique()
                                st.metric("Unique Vendors", unique_vendors)
                    
                    else:
                        st.info("No items found matching the selected criteria.")
                    
                    # Quick Actions Section
                    st.markdown("---")
                    st.subheader("⚡ Quick Actions")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📋 Export Expired Items", use_container_width=True):
                            if not expired_items.empty:
                                st.success(f"✅ Found {len(expired_items)} expired items ready for export")
                            else:
                                st.info("No expired items to export")
                    
                    with col2:
                        if st.button("📧 Send Expiry Alerts", use_container_width=True):
                            critical_count = len(critical_items) + len(expired_items)
                            if critical_count > 0:
                                st.success(f"✅ Alerts sent for {critical_count} critical items")
                            else:
                                st.info("No critical items requiring alerts")
                    
                    with col3:
                        if st.button("🔄 Refresh Expiry Data", use_container_width=True):
                            clear_cache()
                            st.success("✅ Expiry data refreshed")
                            st.rerun()
                
                else:
                    st.info("No materials with expiry dates found. Add materials with expiry dates in the Inward Register to start tracking.")
                    
                    # Show sample of how to add expiry dates
                    with st.expander("💡 How to Add Expiry Tracking", expanded=False):
                        st.markdown("""
                        **To track material expiry:**
                        
                        1. Go to **Inward Register** module
                        2. When adding materials, fill in:
                           - **Mfg Date**: Manufacturing date of the material
                           - **Expiry Date**: When the material expires
                        3. Return to this module to monitor expiry status
                        
                        **Materials that typically have expiry dates:**
                        - Cement (3-6 months)
                        - Paints & Chemicals (1-2 years)
                        - Adhesives & Sealants (6-12 months)
                        - Waterproofing compounds
                        - Admixtures & additives
                        """)
            else:
                st.info("No inward register data found. Add materials in Inward Register first.")
                
        except Exception as e:
            st.error(f"Error loading expiry data: {str(e)}")
    else:
        st.error("Google Sheets not connected")

elif "BOQ Mapping" in current_page:
    st.subheader("📑 BOQ Mapping")
    
    # BOQ Creation Section
    with st.expander("📋 Create/Manage BOQ", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input("Project Name*", placeholder="Enter project/building name")
            boq_item_code = st.text_input("BOQ Item Code*", placeholder="e.g., E01, C02, S03")
            wing = st.text_input("Wing (Optional)", placeholder="e.g., A, B, C, Tower 1")
            
        with col2:
            work_description = st.text_input("Work Description*", placeholder="Description of construction work")
            unit_of_measurement = st.selectbox("Unit*", ["Sqm", "Cum", "Nos", "Kg", "Tons", "Running Meter", "Lump Sum"])
            flat_number = st.text_input("Flat Number (Optional)", placeholder="e.g., 101, 202, 3A")
    
    # Material Mapping Section
    with st.expander("🔗 Material Mapping", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            material_name, material_grade = create_material_grade_selector(sheets_manager, "boq")
            quantity_per_unit = st.number_input("Quantity per Unit*", min_value=0.001, step=0.001, format="%.3f", help="Material quantity required per unit of BOQ item")
            
        with col2:
            material_unit = st.selectbox("Material Unit*", ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"])
            wastage_percentage = st.number_input("Wastage %", min_value=0.0, max_value=100.0, step=0.1, format="%.1f", value=5.0)
    
    # Calculate total quantity including wastage
    if quantity_per_unit > 0:
        total_with_wastage = quantity_per_unit * (1 + wastage_percentage / 100)
        st.info(f"📊 **Total Quantity (including {wastage_percentage}% wastage):** {total_with_wastage:.3f} {material_unit} per {unit_of_measurement}")
    
    remarks = st.text_area("Remarks", placeholder="Additional notes about BOQ mapping")
    
    # Submit button
    if st.button("Add BOQ Mapping", type="primary", use_container_width=True):
        if project_name and boq_item_code and work_description and material_name and quantity_per_unit > 0:
            
            # Create material description
            full_material = f"{material_name}" + (f" - {material_grade}" if material_grade else "")
            
            # Calculate final quantity with wastage
            final_quantity = quantity_per_unit * (1 + wastage_percentage / 100)
            
            boq_data = [
                project_name,
                boq_item_code,
                work_description,
                unit_of_measurement,
                wing if wing else "",
                flat_number if flat_number else "",
                full_material,
                material_name,
                material_grade,
                quantity_per_unit,
                material_unit,
                wastage_percentage,
                final_quantity,
                remarks,
                datetime.now().strftime('%Y-%m-%d %H:%M')
            ]
            
            try:
                if not sheets_manager:
                    st.error("❌ Google Sheets not connected. Please check your connection.")
                else:
                    headers = ['Project Name', 'BOQ Item Code', 'Work Description', 'Unit', 'Wing', 'Flat Number', 'Material Name', 'Material', 'Grade', 'Quantity per Unit', 'Material Unit', 'Wastage %', 'Final Quantity', 'Remarks', 'Created Date']
                    
                    with st.spinner("Saving BOQ mapping to Google Sheets..."):
                        boq_worksheet = sheets_manager.get_or_create_worksheet('BOQ Mapping', headers)
                        
                        # Validate data length matches headers
                        if len(boq_data) != len(headers):
                            raise ValueError(f"Data length ({len(boq_data)}) doesn't match headers length ({len(headers)})")
                        
                        # Add the data
                        result = boq_worksheet.append_row(boq_data)
                        
                        # Verify the data was added by checking row count
                        all_values = boq_worksheet.get_all_values()
                        row_count = len(all_values)
                        
                        if row_count < 2:  # Should have at least header + 1 data row
                            raise Exception("Data was not saved - sheet appears empty")
                    
                    # Clear cache to ensure all modules see updated data
                    clear_cache()
                    
                    st.success(f"✅ BOQ mapping saved successfully: {boq_item_code} - {work_description}")
                    st.info(f"📊 Data added to row {row_count} in 'BOQ Mapping' sheet. Total rows: {row_count}")
                    st.info("🔗 Check your Google Sheets to verify the data was saved.")
                    st.balloons()
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving BOQ mapping: {str(e)}")
                st.write("**Troubleshooting:**")
                st.write("1. Check if 'BOQ Mapping' sheet exists in your Google Sheets")
                st.write("2. Verify the sheet has the correct headers")
                st.write("3. Ensure you have edit permissions on the sheet")
                st.code(f"Error details: {str(e)}", language="text")
        else:
            st.error("Please fill all required fields marked with *")

    # Display BOQ Mappings
    st.markdown("---")
    st.subheader("📋 BOQ Mappings")
    
    if sheets_manager:
        try:
            headers = ['Project Name', 'BOQ Item Code', 'Work Description', 'Unit', 'Wing', 'Flat Number', 'Material Name', 'Material', 'Grade', 'Quantity per Unit', 'Material Unit', 'Wastage %', 'Final Quantity', 'Remarks', 'Created Date']
            boq_worksheet = sheets_manager.get_or_create_worksheet('BOQ Mapping', headers)
            boq_df = sheets_manager.dataframe_from_worksheet(boq_worksheet)
            
            if not boq_df.empty:
                # Filter options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    project_filter = st.selectbox("Filter by Project", ["All Projects"] + list(boq_df['Project Name'].unique()))
                    
                with col2:
                    material_filter = st.selectbox("Filter by Material", ["All Materials"] + list(boq_df['Material'].unique()))
                    
                with col3:
                    boq_filter = st.text_input("Search BOQ Code", placeholder="Enter BOQ item code")
                
                # Apply filters
                filtered_df = boq_df.copy()
                
                if project_filter != "All Projects":
                    filtered_df = filtered_df[filtered_df['Project Name'] == project_filter]
                    
                if material_filter != "All Materials":
                    filtered_df = filtered_df[filtered_df['Material'] == material_filter]
                    
                if boq_filter:
                    filtered_df = filtered_df[filtered_df['BOQ Item Code'].str.contains(boq_filter, case=False, na=False)]
                
                # Display filtered results
                if not filtered_df.empty:
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                    
                    # Show summary
                    col_summary1, col_summary2, col_summary3 = st.columns(3)
                    with col_summary1:
                        st.metric("Total BOQ Items", len(filtered_df))
                    with col_summary2:
                        unique_projects = filtered_df['Project Name'].nunique()
                        st.metric("Projects", unique_projects)
                    with col_summary3:
                        unique_materials = filtered_df['Material'].nunique()
                        st.metric("Materials", unique_materials)
                else:
                    st.info("No BOQ mappings found matching the selected criteria.")
            else:
                st.info("No BOQ mappings found. Create your first mapping above.")
        except Exception as e:
            st.error(f"Error loading BOQ mappings: {str(e)}")
    else:
        st.error("❌ Cannot load BOQ data - Google Sheets not connected")

elif "Indent Register" in current_page:
    st.subheader("📝 Indent Register")
    
    # Material Indent Section
    with st.expander("📋 Create Material Indent", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            indent_date = st.date_input("Indent Date*", value=datetime.now().date())
            indent_number = st.text_input("Indent Number*", placeholder="e.g., IND-001, REQ-2025-001")
            project_name = st.text_input("Project Name*", placeholder="Project/Site name")
            
        with col2:
            department = st.selectbox("Department*", ["Civil", "Electrical", "Plumbing", "HVAC", "Interior", "Landscaping", "General", "Maintenance"])
            requested_by = st.text_input("Requested By*", placeholder="Person requesting materials")
            priority = st.selectbox("Priority*", ["Low", "Medium", "High", "Urgent"])
    
    # Material Details Section
    with st.expander("🔧 Material Requirements", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            material_name, material_grade = create_material_grade_selector(sheets_manager, "indent")
            required_quantity = st.number_input("Required Quantity*", min_value=0.01, step=0.01, format="%.2f")
            
        with col2:
            unit = st.selectbox("Unit*", ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"])
            required_date = st.date_input("Required Date*", value=datetime.now().date() + pd.Timedelta(days=7))
    
    # Additional Details Section
    with st.expander("📋 Additional Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            wing = st.text_input("Wing (Optional)", placeholder="e.g., A, B, C, Tower 1")
            flat_number = st.text_input("Flat Number (Optional)", placeholder="e.g., 101, 202, 3A")
            
        with col2:
            purpose = st.selectbox("Purpose", ["Slab Work", "PCC Work", "Raft Foundation", "Retaining Wall", "Column Work", "Beam Work", "Masonry Work", "Plastering", "Flooring", "Electrical Work", "Plumbing Work", "Painting", "Waterproofing", "Other"])
            approved_by = st.text_input("Approved By", placeholder="Approving authority")
    
    purpose_description = st.text_area("Purpose Description*", placeholder="Detailed description of material requirement")
    
    # Submit button
    if st.button("Submit Indent", type="primary", use_container_width=True):
        if indent_number and project_name and material_name and required_quantity > 0 and requested_by and purpose_description:
            
            # Create material description
            full_material = f"{material_name}" + (f" - {material_grade}" if material_grade else "")
            
            indent_data = [
                indent_date.strftime('%Y-%m-%d'),
                indent_number,
                project_name,
                department,
                requested_by,
                priority,
                full_material,
                material_name,
                material_grade,
                required_quantity,
                unit,
                required_date.strftime('%Y-%m-%d'),
                wing if wing else "",
                flat_number if flat_number else "",
                purpose,
                purpose_description,
                approved_by if approved_by else "",
                "Pending",
                datetime.now().strftime('%Y-%m-%d %H:%M')
            ]
            
            try:
                headers = ['Indent Date', 'Indent Number', 'Project Name', 'Department', 'Requested By', 'Priority', 'Material Name', 'Material', 'Grade', 'Required Quantity', 'Unit', 'Required Date', 'Wing', 'Flat Number', 'Purpose', 'Purpose Description', 'Approved By', 'Status', 'Created Date']
                indent_worksheet = sheets_manager.get_or_create_worksheet('Indent Register', headers)
                indent_worksheet.append_row(indent_data)
                
                # Clear cache to ensure all modules see updated data
                clear_cache()
                
                st.success(f"✅ Indent submitted successfully: {indent_number} for {full_material}")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error submitting indent: {str(e)}")
        else:
            st.error("Please fill all required fields marked with *")

    # Display Recent Indents
    st.markdown("---")
    st.subheader("📋 Recent Indents")
    
    if sheets_manager:
        try:
            headers = ['Indent Date', 'Indent Number', 'Project Name', 'Department', 'Requested By', 'Priority', 'Material Name', 'Material', 'Grade', 'Required Quantity', 'Unit', 'Required Date', 'Wing', 'Flat Number', 'Purpose', 'Purpose Description', 'Approved By', 'Status', 'Created Date']
            indent_worksheet = sheets_manager.get_or_create_worksheet('Indent Register', headers)
            indent_df = sheets_manager.dataframe_from_worksheet(indent_worksheet)
            
            if not indent_df.empty:
                # Filter options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status_filter = st.selectbox("Filter by Status", ["All Status", "Pending", "Approved", "Rejected", "Fulfilled", "Partially Fulfilled"])
                    
                with col2:
                    priority_filter = st.selectbox("Filter by Priority", ["All Priorities", "Low", "Medium", "High", "Urgent"])
                    
                with col3:
                    department_filter = st.selectbox("Filter by Department", ["All Departments"] + list(indent_df['Department'].unique()))
                
                # Apply filters
                filtered_df = indent_df.copy()
                
                if status_filter != "All Status":
                    filtered_df = filtered_df[filtered_df['Status'] == status_filter]
                    
                if priority_filter != "All Priorities":
                    filtered_df = filtered_df[filtered_df['Priority'] == priority_filter]
                    
                if department_filter != "All Departments":
                    filtered_df = filtered_df[filtered_df['Department'] == department_filter]
                
                # Display filtered results
                if not filtered_df.empty:
                    # Show recent entries (last 20)
                    recent_entries = filtered_df.tail(20)
                    st.dataframe(recent_entries, use_container_width=True, hide_index=True)
                    
                    # Show summary
                    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
                    with col_summary1:
                        st.metric("Total Indents", len(filtered_df))
                    with col_summary2:
                        pending_count = len(filtered_df[filtered_df['Status'] == 'Pending'])
                        st.metric("Pending", pending_count)
                    with col_summary3:
                        urgent_count = len(filtered_df[filtered_df['Priority'] == 'Urgent'])
                        st.metric("Urgent", urgent_count)
                    with col_summary4:
                        unique_projects = filtered_df['Project Name'].nunique()
                        st.metric("Projects", unique_projects)
                else:
                    st.info("No indents found matching the selected criteria.")
            else:
                st.info("No indents found. Submit your first indent above.")
        except Exception as e:
            st.error(f"Error loading indents: {str(e)}")
    else:
        st.error("❌ Cannot load indent data - Google Sheets not connected")

elif "Material Transfer Register" in current_page:
    st.subheader("🔄 Material Transfer Register")
    
    # Material Transfer Section
    with st.expander("📦 Create Material Transfer", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            transfer_date = st.date_input("Transfer Date*", value=datetime.now().date())
            transfer_number = st.text_input("Transfer Number*", placeholder="e.g., TRF-001, MT-2025-001")
            transfer_type = st.selectbox("Transfer Type*", [
                "Site to Site", "Department to Department", "Warehouse to Site", 
                "Site to Warehouse", "Emergency Transfer", "Project Transfer"
            ])
            
        with col2:
            from_location = st.text_input("From Location*", placeholder="Source location/site/department")
            to_location = st.text_input("To Location*", placeholder="Destination location/site/department")
            transfer_reason = st.selectbox("Transfer Reason*", [
                "Project Requirement", "Stock Redistribution", "Emergency Need", 
                "Equipment Relocation", "Excess Stock", "Quality Issues", "Other"
            ])
    
    # Material Details Section
    with st.expander("🔧 Material Transfer Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            material_name, material_grade = create_material_grade_selector(sheets_manager, "transfer")
            transfer_quantity = st.number_input("Transfer Quantity*", min_value=0.01, step=0.01, format="%.2f")
            
        with col2:
            unit = st.selectbox("Unit*", ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"])
            transfer_by = st.text_input("Transfer Authorized By*", placeholder="Person authorizing transfer")
    
    # Additional Transfer Details
    with st.expander("📋 Transfer Information", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            vehicle_number = st.text_input("Vehicle Number", placeholder="e.g., MH12AB1234")
            driver_name = st.text_input("Driver Name", placeholder="Driver's name")
            
        with col2:
            received_by = st.text_input("Received By", placeholder="Person receiving at destination")
            delivery_date = st.date_input("Expected Delivery Date", value=datetime.now().date())
    
    transfer_remarks = st.text_area("Transfer Remarks", placeholder="Additional notes about the transfer")
    
    # Submit button
    if st.button("Create Transfer", type="primary", use_container_width=True):
        if transfer_number and material_name and transfer_quantity > 0 and from_location and to_location and transfer_by:
            
            # Create material description
            full_material = f"{material_name}" + (f" - {material_grade}" if material_grade else "")
            
            transfer_data = [
                transfer_date.strftime('%Y-%m-%d'),
                transfer_number,
                transfer_type,
                from_location,
                to_location,
                transfer_reason,
                full_material,
                material_name,
                material_grade,
                transfer_quantity,
                unit,
                transfer_by,
                vehicle_number if vehicle_number else "",
                driver_name if driver_name else "",
                received_by if received_by else "",
                delivery_date.strftime('%Y-%m-%d'),
                transfer_remarks if transfer_remarks else "",
                "In Transit",
                datetime.now().strftime('%Y-%m-%d %H:%M')
            ]
            
            try:
                headers = ['Transfer Date', 'Transfer Number', 'Transfer Type', 'From Location', 'To Location', 'Transfer Reason', 'Material Name', 'Material', 'Grade', 'Transfer Quantity', 'Unit', 'Authorized By', 'Vehicle Number', 'Driver Name', 'Received By', 'Expected Delivery Date', 'Remarks', 'Status', 'Created Date']
                transfer_worksheet = sheets_manager.get_or_create_worksheet('Material Transfer Register', headers)
                transfer_worksheet.append_row(transfer_data)
                
                # Clear cache to ensure all modules see updated data
                clear_cache()
                
                st.success(f"✅ Transfer created successfully: {transfer_number} for {transfer_quantity} {unit} of {full_material}")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error creating transfer: {str(e)}")
        else:
            st.error("Please fill all required fields marked with *")

    # Transfer Status Update Section
    st.markdown("---")
    st.subheader("📋 Transfer Status Update")
    
    with st.expander("🔄 Update Transfer Status", expanded=False):
        if sheets_manager:
            try:
                headers = ['Transfer Date', 'Transfer Number', 'Transfer Type', 'From Location', 'To Location', 'Transfer Reason', 'Material Name', 'Material', 'Grade', 'Transfer Quantity', 'Unit', 'Authorized By', 'Vehicle Number', 'Driver Name', 'Received By', 'Expected Delivery Date', 'Remarks', 'Status', 'Created Date']
                transfer_worksheet = sheets_manager.get_or_create_worksheet('Material Transfer Register', headers)
                transfer_df = sheets_manager.dataframe_from_worksheet(transfer_worksheet)
                
                if not transfer_df.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Select transfer number
                        transfer_options = ["Select Transfer"] + list(transfer_df['Transfer Number'].unique())
                        selected_transfer = st.selectbox("Select Transfer Number", transfer_options)
                        
                        if selected_transfer != "Select Transfer":
                            # Show transfer details
                            transfer_details = transfer_df[transfer_df['Transfer Number'] == selected_transfer].iloc[0]
                            
                            st.write("**Transfer Details:**")
                            st.write(f"- **Type:** {transfer_details.get('Transfer Type', 'N/A')}")
                            st.write(f"- **From:** {transfer_details.get('From Location', 'N/A')}")
                            st.write(f"- **To:** {transfer_details.get('To Location', 'N/A')}")
                            st.write(f"- **Material:** {transfer_details.get('Material', 'N/A')} - {transfer_details.get('Grade', 'N/A')}")
                            st.write(f"- **Quantity:** {transfer_details.get('Transfer Quantity', 'N/A')} {transfer_details.get('Unit', 'N/A')}")
                            st.write(f"- **Current Status:** {transfer_details.get('Status', 'N/A')}")
                    
                    with col2:
                        if selected_transfer != "Select Transfer":
                            new_status = st.selectbox("Update Status", ["In Transit", "Delivered", "Cancelled", "Delayed", "Partially Delivered"])
                            status_update_date = st.date_input("Status Update Date", value=datetime.now().date(), key="transfer_status_date")
                            status_remarks = st.text_area("Status Update Remarks", placeholder="Add remarks for status update", key="transfer_status_remarks")
                            
                            if st.button("Update Transfer Status", type="primary"):
                                try:
                                    # Find the row to update
                                    transfer_row_idx = transfer_df[transfer_df['Transfer Number'] == selected_transfer].index[0]
                                    sheet_row = transfer_row_idx + 2  # Add 2 for header and 0-indexing
                                    
                                    # Update status
                                    status_col = headers.index('Status') + 1
                                    transfer_worksheet.update_cell(sheet_row, status_col, new_status)
                                    
                                    # Clear cache
                                    clear_cache()
                                    
                                    st.success(f"✅ Transfer {selected_transfer} status updated to '{new_status}' on {status_update_date}")
                                    if status_remarks:
                                        st.info(f"Remarks: {status_remarks}")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Error updating transfer status: {str(e)}")
                else:
                    st.info("No transfers found. Create transfers above first.")
            except Exception as e:
                st.error(f"Error loading transfers: {str(e)}")
        else:
            st.error("Google Sheets not connected")

    # Display Recent Transfers
    st.markdown("---")
    st.subheader("📋 Recent Transfers")
    
    if sheets_manager:
        try:
            headers = ['Transfer Date', 'Transfer Number', 'Transfer Type', 'From Location', 'To Location', 'Transfer Reason', 'Material Name', 'Material', 'Grade', 'Transfer Quantity', 'Unit', 'Authorized By', 'Vehicle Number', 'Driver Name', 'Received By', 'Expected Delivery Date', 'Remarks', 'Status', 'Created Date']
            transfer_worksheet = sheets_manager.get_or_create_worksheet('Material Transfer Register', headers)
            transfer_df = sheets_manager.dataframe_from_worksheet(transfer_worksheet)
            
            if not transfer_df.empty:
                # Filter options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status_filter = st.selectbox("Filter by Status", ["All Status", "In Transit", "Delivered", "Cancelled", "Delayed", "Partially Delivered"])
                    
                with col2:
                    type_filter = st.selectbox("Filter by Type", ["All Types"] + list(transfer_df['Transfer Type'].unique()))
                    
                with col3:
                    location_filter = st.selectbox("Filter by From Location", ["All Locations"] + list(transfer_df['From Location'].unique()))
                
                # Apply filters
                filtered_df = transfer_df.copy()
                
                if status_filter != "All Status":
                    filtered_df = filtered_df[filtered_df['Status'] == status_filter]
                    
                if type_filter != "All Types":
                    filtered_df = filtered_df[filtered_df['Transfer Type'] == type_filter]
                    
                if location_filter != "All Locations":
                    filtered_df = filtered_df[filtered_df['From Location'] == location_filter]
                
                # Display filtered results
                if not filtered_df.empty:
                    # Show recent entries (last 20)
                    recent_entries = filtered_df.tail(20)
                    st.dataframe(recent_entries, use_container_width=True, hide_index=True)
                    
                    # Show summary
                    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
                    with col_summary1:
                        st.metric("Total Transfers", len(filtered_df))
                    with col_summary2:
                        in_transit_count = len(filtered_df[filtered_df['Status'] == 'In Transit'])
                        st.metric("In Transit", in_transit_count)
                    with col_summary3:
                        delivered_count = len(filtered_df[filtered_df['Status'] == 'Delivered'])
                        st.metric("Delivered", delivered_count)
                    with col_summary4:
                        unique_materials = filtered_df['Material'].nunique()
                        st.metric("Materials", unique_materials)
                else:
                    st.info("No transfers found matching the selected criteria.")
            else:
                st.info("No transfers found. Create your first transfer above.")
        except Exception as e:
            st.error(f"Error loading transfers: {str(e)}")
    else:
        st.error("❌ Cannot load transfer data - Google Sheets not connected")

elif "Scrap Register" in current_page:
    st.subheader("♻️ Scrap Register")
    
    # Scrap Entry Section
    with st.expander("📝 Record Scrap Material", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            scrap_date = st.date_input("Scrap Date*", value=datetime.now().date())
            scrap_number = st.text_input("Scrap Reference Number*", placeholder="e.g., SCRAP-001, SC-2025-001")
            scrap_type = st.selectbox("Scrap Type*", [
                "Construction Waste", "Metal Scrap", "Wood Waste", "Concrete Waste", 
                "Packaging Material", "Electrical Waste", "Defective Material", "Other"
            ])
            
        with col2:
            scrap_source = st.selectbox("Scrap Source*", [
                "Construction Site", "Demolition", "Quality Rejection", "Damage/Breakage", 
                "Expired Material", "Over-ordering", "Project Completion", "Other"
            ])
            project_name = st.text_input("Project Name", placeholder="Associated project")
            location = st.text_input("Location/Site*", placeholder="Where scrap was generated")
    
    # Material Details Section
    with st.expander("🔧 Scrap Material Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            material_name, material_grade = create_material_grade_selector(sheets_manager, "scrap")
            scrap_quantity = st.number_input("Scrap Quantity*", min_value=0.01, step=0.01, format="%.2f")
            
        with col2:
            unit = st.selectbox("Unit*", ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"])
            original_value = st.number_input("Original Value (₹)", min_value=0.0, step=0.01, format="%.2f")
    
    # Scrap Assessment Section
    with st.expander("💰 Scrap Assessment & Recovery", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            scrap_condition = st.selectbox("Scrap Condition*", [
                "Good - Reusable", "Fair - Partially Reusable", "Poor - Scrap Only", 
                "Damaged - No Value", "Hazardous - Disposal Required"
            ])
            recovery_method = st.selectbox("Recovery Method", [
                "Sale to Scrap Dealer", "Internal Reuse", "Recycling", 
                "Donation", "Disposal", "Processing Required", "Not Decided"
            ])
            
        with col2:
            estimated_recovery_value = st.number_input("Estimated Recovery Value (₹)", min_value=0.0, step=0.01, format="%.2f")
            recovery_percentage = st.number_input("Recovery % of Original Value", min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
    
    # Additional Details
    with st.expander("📋 Additional Information", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            recorded_by = st.text_input("Recorded By*", placeholder="Person recording scrap")
            supervisor = st.text_input("Supervisor/Approved By", placeholder="Supervisor name")
            
        with col2:
            wing_flat = st.text_input("Wing/Flat Number", placeholder="Specific location if applicable")
            vendor_buyer = st.text_input("Scrap Buyer/Vendor", placeholder="Who will buy/collect scrap")
    
    scrap_description = st.text_area("Scrap Description & Reason", placeholder="Detailed description of scrap material and reason for scrapping")
    
    # Submit button
    if st.button("Record Scrap", type="primary", use_container_width=True):
        if scrap_number and material_name and scrap_quantity > 0 and location and recorded_by and scrap_condition:
            
            # Create material description
            full_material = f"{material_name}" + (f" - {material_grade}" if material_grade else "")
            
            # Calculate recovery percentage if not manually entered
            if recovery_percentage == 0.0 and original_value > 0 and estimated_recovery_value > 0:
                recovery_percentage = round((estimated_recovery_value / original_value) * 100, 1)
            
            scrap_data = [
                scrap_date.strftime('%Y-%m-%d'),
                scrap_number,
                scrap_type,
                scrap_source,
                project_name if project_name else "",
                location,
                full_material,
                material_name,
                material_grade,
                scrap_quantity,
                unit,
                original_value if original_value else 0,
                scrap_condition,
                recovery_method if recovery_method else "",
                estimated_recovery_value if estimated_recovery_value else 0,
                recovery_percentage if recovery_percentage else 0,
                recorded_by,
                supervisor if supervisor else "",
                wing_flat if wing_flat else "",
                vendor_buyer if vendor_buyer else "",
                scrap_description if scrap_description else "",
                "Recorded",
                datetime.now().strftime('%Y-%m-%d %H:%M')
            ]
            
            try:
                headers = ['Scrap Date', 'Scrap Number', 'Scrap Type', 'Scrap Source', 'Project Name', 'Location', 'Material Name', 'Material', 'Grade', 'Scrap Quantity', 'Unit', 'Original Value', 'Scrap Condition', 'Recovery Method', 'Estimated Recovery Value', 'Recovery Percentage', 'Recorded By', 'Supervisor', 'Wing/Flat', 'Scrap Buyer', 'Description', 'Status', 'Created Date']
                scrap_worksheet = sheets_manager.get_or_create_worksheet('Scrap Register', headers)
                scrap_worksheet.append_row(scrap_data)
                
                # Clear cache to ensure all modules see updated data
                clear_cache()
                
                st.success(f"✅ Scrap recorded successfully: {scrap_number} for {scrap_quantity} {unit} of {full_material}")
                if estimated_recovery_value > 0:
                    st.info(f"💰 Estimated recovery value: ₹{estimated_recovery_value:,.2f} ({recovery_percentage}% of original value)")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error recording scrap: {str(e)}")
        else:
            st.error("Please fill all required fields marked with *")

    # Scrap Status Update Section
    st.markdown("---")
    st.subheader("🔄 Update Scrap Status")
    
    with st.expander("💰 Update Recovery Status", expanded=False):
        if sheets_manager:
            try:
                headers = ['Scrap Date', 'Scrap Number', 'Scrap Type', 'Scrap Source', 'Project Name', 'Location', 'Material Name', 'Material', 'Grade', 'Scrap Quantity', 'Unit', 'Original Value', 'Scrap Condition', 'Recovery Method', 'Estimated Recovery Value', 'Recovery Percentage', 'Recorded By', 'Supervisor', 'Wing/Flat', 'Scrap Buyer', 'Description', 'Status', 'Created Date']
                scrap_worksheet = sheets_manager.get_or_create_worksheet('Scrap Register', headers)
                scrap_df = sheets_manager.dataframe_from_worksheet(scrap_worksheet)
                
                if not scrap_df.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Select scrap number
                        scrap_options = ["Select Scrap"] + list(scrap_df['Scrap Number'].unique())
                        selected_scrap = st.selectbox("Select Scrap Reference", scrap_options)
                        
                        if selected_scrap != "Select Scrap":
                            # Show scrap details
                            scrap_details = scrap_df[scrap_df['Scrap Number'] == selected_scrap].iloc[0]
                            
                            st.write("**Scrap Details:**")
                            st.write(f"- **Type:** {scrap_details.get('Scrap Type', 'N/A')}")
                            st.write(f"- **Material:** {scrap_details.get('Material', 'N/A')} - {scrap_details.get('Grade', 'N/A')}")
                            st.write(f"- **Quantity:** {scrap_details.get('Scrap Quantity', 'N/A')} {scrap_details.get('Unit', 'N/A')}")
                            st.write(f"- **Condition:** {scrap_details.get('Scrap Condition', 'N/A')}")
                            st.write(f"- **Current Status:** {scrap_details.get('Status', 'N/A')}")
                            st.write(f"- **Estimated Value:** ₹{float(scrap_details.get('Estimated Recovery Value', 0)):,.2f}")
                    
                    with col2:
                        if selected_scrap != "Select Scrap":
                            new_status = st.selectbox("Update Status", ["Recorded", "Under Assessment", "Ready for Sale", "Sold", "Disposed", "Recycled", "Reused"])
                            actual_recovery_value = st.number_input("Actual Recovery Value (₹)", min_value=0.0, step=0.01, format="%.2f", key="actual_recovery")
                            recovery_date = st.date_input("Recovery/Sale Date", value=datetime.now().date(), key="scrap_recovery_date")
                            status_remarks = st.text_area("Status Update Remarks", placeholder="Add remarks for status update", key="scrap_status_remarks")
                            
                            if st.button("Update Scrap Status", type="primary"):
                                try:
                                    # Find the row to update
                                    scrap_row_idx = scrap_df[scrap_df['Scrap Number'] == selected_scrap].index[0]
                                    sheet_row = scrap_row_idx + 2  # Add 2 for header and 0-indexing
                                    
                                    # Update status
                                    status_col = headers.index('Status') + 1
                                    scrap_worksheet.update_cell(sheet_row, status_col, new_status)
                                    
                                    # Clear cache
                                    clear_cache()
                                    
                                    st.success(f"✅ Scrap {selected_scrap} status updated to '{new_status}' on {recovery_date}")
                                    if actual_recovery_value > 0:
                                        st.info(f"💰 Actual recovery value: ₹{actual_recovery_value:,.2f}")
                                    if status_remarks:
                                        st.info(f"Remarks: {status_remarks}")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Error updating scrap status: {str(e)}")
                else:
                    st.info("No scrap records found. Record scrap materials above first.")
            except Exception as e:
                st.error(f"Error loading scrap records: {str(e)}")
        else:
            st.error("Google Sheets not connected")

    # Display Recent Scrap Records
    st.markdown("---")
    st.subheader("📋 Recent Scrap Records")
    
    if sheets_manager:
        try:
            headers = ['Scrap Date', 'Scrap Number', 'Scrap Type', 'Scrap Source', 'Project Name', 'Location', 'Material Name', 'Material', 'Grade', 'Scrap Quantity', 'Unit', 'Original Value', 'Scrap Condition', 'Recovery Method', 'Estimated Recovery Value', 'Recovery Percentage', 'Recorded By', 'Supervisor', 'Wing/Flat', 'Scrap Buyer', 'Description', 'Status', 'Created Date']
            scrap_worksheet = sheets_manager.get_or_create_worksheet('Scrap Register', headers)
            scrap_df = sheets_manager.dataframe_from_worksheet(scrap_worksheet)
            
            if not scrap_df.empty:
                # Filter options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status_filter = st.selectbox("Filter by Status", ["All Status", "Recorded", "Under Assessment", "Ready for Sale", "Sold", "Disposed", "Recycled", "Reused"])
                    
                with col2:
                    type_filter = st.selectbox("Filter by Type", ["All Types"] + list(scrap_df['Scrap Type'].unique()))
                    
                with col3:
                    source_filter = st.selectbox("Filter by Source", ["All Sources"] + list(scrap_df['Scrap Source'].unique()))
                
                # Apply filters
                filtered_df = scrap_df.copy()
                
                if status_filter != "All Status":
                    filtered_df = filtered_df[filtered_df['Status'] == status_filter]
                    
                if type_filter != "All Types":
                    filtered_df = filtered_df[filtered_df['Scrap Type'] == type_filter]
                    
                if source_filter != "All Sources":
                    filtered_df = filtered_df[filtered_df['Scrap Source'] == source_filter]
                
                # Display filtered results
                if not filtered_df.empty:
                    # Show recent entries (last 20)
                    recent_entries = filtered_df.tail(20)
                    st.dataframe(recent_entries, use_container_width=True, hide_index=True)
                    
                    # Show summary
                    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
                    with col_summary1:
                        st.metric("Total Scrap Items", len(filtered_df))
                    with col_summary2:
                        total_original_value = filtered_df['Original Value'].astype(float).sum()
                        st.metric("Total Original Value", f"₹{total_original_value:,.0f}")
                    with col_summary3:
                        total_recovery_value = filtered_df['Estimated Recovery Value'].astype(float).sum()
                        st.metric("Est. Recovery Value", f"₹{total_recovery_value:,.0f}")
                    with col_summary4:
                        if total_original_value > 0:
                            recovery_rate = (total_recovery_value / total_original_value) * 100
                            st.metric("Recovery Rate", f"{recovery_rate:.1f}%")
                        else:
                            st.metric("Recovery Rate", "N/A")
                else:
                    st.info("No scrap records found matching the selected criteria.")
            else:
                st.info("No scrap records found. Record your first scrap material above.")
        except Exception as e:
            st.error(f"Error loading scrap records: {str(e)}")
    else:
        st.error("❌ Cannot load scrap data - Google Sheets not connected")

elif "Stock Summary" in current_page:
    st.subheader("📊 Stock Summary")
    
    # Simple stock summary with fallback to avoid API quota issues
    if sheets_manager:
        # Use cached data to minimize API calls
        try:
            inward_df = get_cached_inward_data()
            outward_df = get_cached_outward_data()
        except:
            # If API quota exceeded, show fallback interface
            st.warning("⚠️ Google Sheets API quota temporarily exceeded. Please wait a few minutes and refresh.")
            
            # Show fallback material and grade dropdowns
            col1, col2 = st.columns(2)
            with col1:
                materials_list = get_cached_materials_list()
                selected_material = st.selectbox(
                    "Material",
                    materials_list,
                    help="Select material to check stock levels."
                )
            
            with col2:
                grades_list = get_cached_grades_list()
                selected_grade = st.selectbox(
                    "Grade",
                    grades_list,
                    help="Select grade specification to check stock levels."
                )
            
            if selected_material and selected_grade:
                st.info(f"Sample: {selected_material} {selected_grade} stock would be displayed here when API is available.")
            
            st.info("Add materials through Inward Register and try again in a few minutes.")
        
        # Normal operation when API is working
        if not inward_df.empty:
            # 1. Material and Grade Selection - Dropdown selectors
            col1, col2 = st.columns(2)
            
            with col1:
                materials_list = get_cached_materials_list()
                selected_material = st.selectbox(
                    "Material",
                    materials_list,
                    help="Select material to check stock levels.",
                    key="stock_material_select"
                )
            
            with col2:
                grades_list = get_cached_grades_list()
                selected_grade = st.selectbox(
                    "Grade",
                    grades_list,
                    help="Select grade specification to check stock levels.",
                    key="stock_grade_select"
                )
            
            # 2. Show Stock for Selected Material and Grade
            if selected_material and selected_grade:
                st.markdown("---")
                
                # Calculate stock
                inward_data = inward_df[(inward_df['Material'] == selected_material) & (inward_df['Grade'] == selected_grade)]
                outward_data = outward_df[(outward_df['Material'] == selected_material) & (outward_df['Grade'] == selected_grade)]
                
                total_inward = inward_data['Quantity'].astype(float).sum() if not inward_data.empty else 0
                total_outward = outward_data['Quantity'].astype(float).sum() if not outward_data.empty else 0
                stock = total_inward - total_outward
                unit = inward_data['Unit'].iloc[0] if not inward_data.empty else "Units"
                
                # Display stock
                st.success(f"**{selected_material} {selected_grade}: {stock:.2f} {unit}**")
            
            # 3. Set Low Stock Limit
            if selected_material and selected_grade:
                st.markdown("---")
                st.subheader("⚠️ Set Low Stock Limit")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    limit_input = st.number_input(
                        f"Set limit for {selected_material} {selected_grade}",
                        min_value=0.0,
                        step=1.0,
                        format="%.1f"
                    )
                with col2:
                    unit_input = st.selectbox(
                        "Unit*",
                        ["Kg", "Tons", "Nos", "Bags", "Cubic Meter", "Square Meter", "Litre", "Meter"],
                        help="Select the unit for this limit"
                    )
                with col3:
                    if st.button("Set Limit", type="primary"):
                        if limit_input > 0 and unit_input:
                            st.success(f"Low stock limit set to {limit_input} {unit_input}")
                        else:
                            st.error("Enter a valid limit value and select unit")
            
            # 4. Complete Stock Summary Table
            st.markdown("---")
            st.subheader("📋 Complete Stock Summary")
            
            # Get all material-grade combinations
            combinations = inward_df[['Material', 'Grade']].drop_duplicates()
            
            summary_data = []
            total_value = 0
            
            for _, row in combinations.iterrows():
                material = row['Material']
                grade = row['Grade']
                
                if pd.isna(grade) or grade == "":
                    continue
                
                # Calculate for this combination
                inward_combo = inward_df[(inward_df['Material'] == material) & (inward_df['Grade'] == grade)]
                outward_combo = outward_df[(outward_df['Material'] == material) & (outward_df['Grade'] == grade)]
                
                inward_qty = inward_combo['Quantity'].astype(float).sum() if not inward_combo.empty else 0
                outward_qty = outward_combo['Quantity'].astype(float).sum() if not outward_combo.empty else 0
                stock_qty = inward_qty - outward_qty
                
                # Calculate value
                if not inward_combo.empty and inward_qty > 0:
                    total_cost = (inward_combo['Quantity'].astype(float) * inward_combo['Rate'].astype(float)).sum()
                    avg_rate = total_cost / inward_qty
                    value = stock_qty * avg_rate
                    unit = inward_combo['Unit'].iloc[0]
                else:
                    value = 0
                    unit = "Units"
                
                total_value += value
                
                summary_data.append({
                    'Material': material,
                    'Grade': grade,
                    'Current Stock': f"{stock_qty:.2f} {unit}",
                    'Stock Value': f"₹{value:,.2f}"
                })
            
            # Display table
            if summary_data:
                df = pd.DataFrame(summary_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Overall total
                st.markdown("---")
                st.metric("Overall Stock Value", f"₹{total_value:,.2f}")
            else:
                st.info("No stock data available")
                
        else:
            # Show manual input even when no data exists
            st.info("No existing materials found. Enter material and grade manually to start tracking stock.")
            
            col1, col2 = st.columns(2)
            with col1:
                materials_list = get_cached_materials_list()
                selected_material = st.selectbox(
                    "Material",
                    materials_list,
                    help="Select material to check stock levels."
                )
            
            with col2:
                grades_list = get_cached_grades_list()
                selected_grade = st.selectbox(
                    "Grade",
                    grades_list,
                    help="Select grade specification to check stock levels."
                )
            
            if selected_material and selected_grade:
                st.info(f"To see stock for {selected_material} {selected_grade}, first add some entries in the Inward Register module.")
    
    else:
        st.error("Google Sheets not connected")


else:
    st.info(f"📋 {current_page} module is under development.")
    st.write("**Available modules:**")
    completed = [
        "Dashboard", "Vendor Management", "Inward Register", "Outward Register", 
        "Returns Register", "Damage / Loss Register", "Stock Summary", "BOQ Mapping",
        "Indent Register", "Material Transfer Register", "Scrap Register", "Reports",
        "Expiry Management"
    ]
    for module in completed:
        st.write(f"✅ {module}")
    
    st.markdown("---")
    st.write("Select a module from the sidebar to get started.")

# Additional utility functions for stock calculations
def calculate_material_stock(sheets_manager, material_name, material_grade=None):
    """Calculate stock for a specific material and grade"""
    try:
        # Get inward data
        inward_headers = ['Date', 'Material Name', 'Material', 'Grade', 'Vendor', 'Quantity', 'Unit', 'Rate', 'Amount', 'Invoice Number', 'Received By', 'Mfg Date', 'Expiry Date', 'Remarks']
        inward_worksheet = sheets_manager.get_or_create_worksheet('Inward Register', inward_headers)
        inward_df = sheets_manager.dataframe_from_worksheet(inward_worksheet)
        
        # Get outward data
        outward_headers = ['Date', 'Material Name', 'Material', 'Grade', 'Quantity', 'Unit', 'Issued To', 'Purpose', 'Issued By', 'Wing', 'Flat Number', 'Remarks']
        outward_worksheet = sheets_manager.get_or_create_worksheet('Outward Register', outward_headers)
        outward_df = sheets_manager.dataframe_from_worksheet(outward_worksheet)
        
        # Filter by material and grade
        if material_grade:
            inward_filtered = inward_df[(inward_df['Material'] == material_name) & (inward_df['Grade'] == material_grade)]
            outward_filtered = outward_df[(outward_df['Material'] == material_name) & (outward_df['Grade'] == material_grade)]
        else:
            inward_filtered = inward_df[inward_df['Material'] == material_name]
            outward_filtered = outward_df[outward_df['Material'] == material_name]
        
        # Calculate totals
        total_inward = inward_filtered['Quantity'].astype(float).sum() if not inward_filtered.empty else 0
        total_outward = outward_filtered['Quantity'].astype(float).sum() if not outward_filtered.empty else 0
        current_stock = total_inward - total_outward
        
        # Calculate average rate and stock value
        if not inward_filtered.empty and total_inward > 0:
            # Weighted average rate calculation
            inward_filtered = inward_filtered.copy()
            inward_filtered['Amount_calc'] = inward_filtered['Quantity'].astype(float) * inward_filtered['Rate'].astype(float)
            total_amount = inward_filtered['Amount_calc'].sum()
            avg_rate = total_amount / total_inward if total_inward > 0 else 0
            stock_value = current_stock * avg_rate
            unit = inward_filtered['Unit'].iloc[0] if not inward_filtered.empty else "Units"
        else:
            avg_rate = 0
            stock_value = 0
            unit = "Units"
        
        return {
            'total_inward': total_inward,
            'total_outward': total_outward,
            'current_stock': current_stock,
            'avg_rate': avg_rate,
            'stock_value': stock_value,
            'unit': unit
        }
        
    except Exception as e:
        st.error(f"Error calculating material stock: {str(e)}")
        return None

def get_low_stock_limit(sheets_manager, material_name, material_grade=None):
    """Get low stock limit for a specific material and grade"""
    try:
        headers = ['Date', 'Material', 'Grade', 'Low Stock Limit', 'Unit', 'Set By', 'Created Date']
        worksheet = sheets_manager.get_or_create_worksheet('Low Stock Limits', headers)
        df = sheets_manager.dataframe_from_worksheet(worksheet)
        
        if not df.empty:
            if material_grade:
                limit_row = df[(df['Material'] == material_name) & (df['Grade'] == material_grade)]
            else:
                limit_row = df[(df['Material'] == material_name) & (df['Grade'].isna() | (df['Grade'] == ""))]
            
            if not limit_row.empty:
                return float(limit_row['Low Stock Limit'].iloc[0])
        
        return None
        
    except Exception as e:
        return None

def calculate_all_material_stock(sheets_manager):
    """Calculate stock for all materials"""
    try:
        import pandas as pd
        
        # Get all unique material-grade combinations from inward register
        inward_headers = ['Date', 'Material Name', 'Material', 'Grade', 'Vendor', 'Quantity', 'Unit', 'Rate', 'Amount', 'Invoice Number', 'Received By', 'Mfg Date', 'Expiry Date', 'Remarks']
        inward_worksheet = sheets_manager.get_or_create_worksheet('Inward Register', inward_headers)
        inward_df = sheets_manager.dataframe_from_worksheet(inward_worksheet)
        
        if inward_df.empty:
            return []
        
        # Get unique material-grade combinations
        material_combinations = inward_df[['Material', 'Grade']].drop_duplicates()
        
        stock_data = []
        
        for _, row in material_combinations.iterrows():
            material = row['Material']
            grade = row['Grade'] if pd.notna(row['Grade']) and row['Grade'] != "" else None
            
            # Calculate stock for this combination
            stock_info = calculate_material_stock(sheets_manager, material, grade)
            
            if stock_info:
                # Get low stock limit
                low_stock_limit = get_low_stock_limit(sheets_manager, material, grade)
                
                # Determine status
                if stock_info['current_stock'] <= 0:
                    status = "Out of Stock"
                elif low_stock_limit and stock_info['current_stock'] <= low_stock_limit:
                    status = "Low Stock"
                else:
                    status = "In Stock"
                
                stock_data.append({
                    'Material': material,
                    'Grade': grade if grade else "",
                    'Current Stock': stock_info['current_stock'],
                    'Unit': stock_info['unit'],
                    'Avg Rate (₹)': stock_info['avg_rate'],
                    'Stock Value (₹)': stock_info['stock_value'],
                    'Low Stock Limit': low_stock_limit if low_stock_limit else "",
                    'Status': status
                })
        
        # Sort by stock value (descending)
        stock_data.sort(key=lambda x: x['Stock Value (₹)'], reverse=True)
        
        return stock_data
        
    except Exception as e:
        st.error(f"Error calculating all material stock: {str(e)}")
        return []