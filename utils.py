from datetime import datetime, date
import streamlit as st
import pandas as pd

def calculate_amount(quantity, rate):
    """Calculate amount from quantity and rate"""
    try:
        return float(quantity) * float(rate)
    except (ValueError, TypeError):
        return 0.0

def validate_input(value, field_name, required=True):
    """Validate input fields"""
    if required and (value is None or value == ""):
        st.error(f"{field_name} is required")
        return False
    return True

def format_date(date_value):
    """Format date for consistent storage"""
    if isinstance(date_value, date):
        return date_value.strftime('%Y-%m-%d')
    elif isinstance(date_value, datetime):
        return date_value.strftime('%Y-%m-%d')
    elif isinstance(date_value, str):
        return date_value
    else:
        return ""

def format_currency(amount):
    """Format amount as currency"""
    try:
        return f"₹{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

def parse_numeric(value, default=0.0):
    """Parse numeric value with default"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def validate_date_range(start_date, end_date):
    """Validate date range"""
    if start_date > end_date:
        st.error("Start date cannot be later than end date")
        return False
    return True

def safe_divide(numerator, denominator):
    """Safe division with zero check"""
    try:
        return float(numerator) / float(denominator) if float(denominator) != 0 else 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

def filter_dataframe_by_date(df, date_column, start_date, end_date):
    """Filter dataframe by date range"""
    if df.empty or date_column not in df.columns:
        return df
    
    try:
        df[date_column] = pd.to_datetime(df[date_column])
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        return df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]
    except Exception:
        return df

def get_unique_values(df, column):
    """Get unique values from dataframe column"""
    if df.empty or column not in df.columns:
        return []
    return df[column].dropna().unique().tolist()

def calculate_stock_status(current_stock, min_threshold=10):
    """Calculate stock status"""
    if current_stock <= 0:
        return "Out of Stock", "🔴"
    elif current_stock <= min_threshold:
        return "Low Stock", "🟡"
    else:
        return "In Stock", "🟢"

def export_dataframe_to_csv(df, filename):
    """Export dataframe to CSV"""
    try:
        return df.to_csv(index=False)
    except Exception as e:
        st.error(f"Error exporting to CSV: {str(e)}")
        return ""

def sanitize_string(value):
    """Sanitize string input"""
    if isinstance(value, str):
        return value.strip()
    return str(value) if value is not None else ""

def validate_phone_number(phone):
    """Basic phone number validation"""
    if not phone:
        return False
    
    # Remove non-numeric characters
    phone_digits = ''.join(filter(str.isdigit, phone))
    
    # Check if it's a valid length (10 digits for Indian numbers)
    return len(phone_digits) == 10

def validate_email(email):
    """Basic email validation"""
    if not email:
        return True  # Email is optional
    
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_invoice_number():
    """Generate unique invoice number"""
    from datetime import datetime
    return f"INV{datetime.now().strftime('%Y%m%d%H%M%S')}"

def get_materials_from_master(sheets_manager):
    """Get materials list from Material Master sheet"""
    if not sheets_manager:
        return []
    
    try:
        headers = ['Material Name', 'Material Category', 'Unit', 'Description', 'Common Usage', 'Added By', 'Date Added']
        material_worksheet = sheets_manager.get_or_create_worksheet('Material Master', headers)
        materials_df = sheets_manager.dataframe_from_worksheet(material_worksheet)
        
        if not materials_df.empty and 'Material Name' in materials_df.columns:
            # Get unique material names, excluding empty values
            materials = materials_df['Material Name'].dropna().unique().tolist()
            materials = [str(m).strip() for m in materials if str(m).strip()]
            return sorted(materials) if materials else []
        return []
    except Exception as e:
        print(f"Error loading materials from master: {e}")
        return []

def get_grades_from_master(sheets_manager):
    """Get grades list from Grade Master sheet"""
    if not sheets_manager:
        return []
    
    try:
        headers = ['Grade/Specification', 'Material Category', 'Description', 'Common Usage', 'Added By', 'Date Added']
        grade_worksheet = sheets_manager.get_or_create_worksheet('Grade Master', headers)
        grades_df = sheets_manager.dataframe_from_worksheet(grade_worksheet)
        
        if not grades_df.empty and 'Grade/Specification' in grades_df.columns:
            # Get unique grades, excluding empty values
            grades = grades_df['Grade/Specification'].dropna().unique().tolist()
            grades = [str(g).strip() for g in grades if str(g).strip()]
            return sorted(grades) if grades else []
        return []
    except Exception as e:
        print(f"Error loading grades from master: {e}")
        return []

def initialize_default_materials_and_grades(sheets_manager):
    """Initialize Material Master and Grade Master with default data"""
    if not sheets_manager:
        return
    
    try:
        # Default materials
        default_materials = [
            ['Steel', 'Metal', 'Kg/MT', 'Construction steel bars and rods', 'Structural construction, reinforcement', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Cement', 'Binder', 'Bag', 'Portland cement for construction', 'Concrete mixing, masonry', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Sand', 'Aggregate', 'CFT', 'Fine aggregate for construction', 'Concrete mixing, plastering', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Gravel', 'Aggregate', 'CFT', 'Coarse aggregate for construction', 'Concrete mixing, foundation', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Bricks', 'Masonry', 'Nos', 'Clay bricks for construction', 'Wall construction, partition', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Tiles', 'Finishing', 'Sqft', 'Ceramic or stone tiles', 'Flooring, wall cladding', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Paint', 'Finishing', 'Litre', 'Wall and surface paint', 'Interior and exterior finishing', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Wire', 'Electrical', 'Meter', 'Electrical wiring cables', 'Electrical installations', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Pipe', 'Plumbing', 'Meter', 'Water and drainage pipes', 'Plumbing, drainage systems', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Wood', 'Timber', 'CFT', 'Construction timber and wood', 'Formwork, carpentry', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Glass', 'Glazing', 'Sqft', 'Window and door glass', 'Windows, doors, partitions', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Aluminum', 'Metal', 'Kg', 'Aluminum sections and sheets', 'Windows, doors, cladding', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Concrete', 'Premix', 'Cum', 'Ready mix concrete', 'Structural construction', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Marble', 'Stone', 'Sqft', 'Natural marble for finishing', 'Flooring, wall cladding', 'System', datetime.now().strftime('%Y-%m-%d')]
        ]
        
        # Default grades
        default_grades = [
            ['8mm', 'Steel', 'Steel reinforcement bar 8mm diameter', 'Light reinforcement work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['10mm', 'Steel', 'Steel reinforcement bar 10mm diameter', 'Medium reinforcement work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['12mm', 'Steel', 'Steel reinforcement bar 12mm diameter', 'Standard reinforcement work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['16mm', 'Steel', 'Steel reinforcement bar 16mm diameter', 'Heavy reinforcement work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['20mm', 'Steel', 'Steel reinforcement bar 20mm diameter', 'Heavy structural work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['OPC 43', 'Cement', 'Ordinary Portland Cement Grade 43', 'General construction work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['OPC 53', 'Cement', 'Ordinary Portland Cement Grade 53', 'High strength construction', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['PPC', 'Cement', 'Portland Pozzolana Cement', 'Durable construction work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['M Sand', 'Sand', 'Manufactured sand', 'Concrete and plastering work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['River Sand', 'Sand', 'Natural river sand', 'Fine concrete work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['20mm', 'Aggregate', '20mm aggregate stones', 'Concrete work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['12mm', 'Aggregate', '12mm aggregate stones', 'Concrete and road work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['6mm', 'Aggregate', '6mm aggregate stones', 'Fine concrete work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Red Brick', 'Bricks', 'Standard red clay bricks', 'Wall construction', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['Fly Ash Brick', 'Bricks', 'Eco-friendly fly ash bricks', 'Modern construction', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['2x2 feet', 'Tiles', 'Standard 2x2 feet tiles', 'Flooring work', 'System', datetime.now().strftime('%Y-%m-%d')],
            ['1x1 feet', 'Tiles', 'Small 1x1 feet tiles', 'Detailed flooring work', 'System', datetime.now().strftime('%Y-%m-%d')]
        ]
        
        # Initialize Material Master
        material_headers = ['Material Name', 'Material Category', 'Unit', 'Description', 'Common Usage', 'Added By', 'Date Added']
        material_worksheet = sheets_manager.get_or_create_worksheet('Material Master', material_headers)
        
        # Check if materials already exist
        materials_df = sheets_manager.dataframe_from_worksheet(material_worksheet)
        if materials_df.empty or len(materials_df) < 5:  # If less than 5 materials, initialize
            # Clear and add headers
            material_worksheet.clear()
            material_worksheet.append_row(material_headers)
            
            # Add default materials
            for material_row in default_materials:
                material_worksheet.append_row(material_row)
            print("✅ Initialized Material Master with default materials")
        
        # Initialize Grade Master
        grade_headers = ['Grade/Specification', 'Material Category', 'Description', 'Common Usage', 'Added By', 'Date Added']
        grade_worksheet = sheets_manager.get_or_create_worksheet('Grade Master', grade_headers)
        
        # Check if grades already exist
        grades_df = sheets_manager.dataframe_from_worksheet(grade_worksheet)
        if grades_df.empty or len(grades_df) < 5:  # If less than 5 grades, initialize
            # Clear and add headers
            grade_worksheet.clear()
            grade_worksheet.append_row(grade_headers)
            
            # Add default grades
            for grade_row in default_grades:
                grade_worksheet.append_row(grade_row)
            print("✅ Initialized Grade Master with default grades")
            
    except Exception as e:
        print(f"Error initializing default materials and grades: {e}")

def add_new_material(sheets_manager, material_name, category, description, unit, usage=""):
    """Add new material to Material Master sheet"""
    if not sheets_manager or not material_name.strip():
        return False, "Invalid input"
    
    try:
        headers = ['Material Name', 'Material Category', 'Unit', 'Description', 'Common Usage', 'Added By', 'Date Added']
        material_worksheet = sheets_manager.get_or_create_worksheet('Material Master', headers)
        
        # Check if material already exists
        materials_df = sheets_manager.dataframe_from_worksheet(material_worksheet)
        if not materials_df.empty and 'Material Name' in materials_df.columns:
            existing_materials = [str(name).strip().lower() for name in materials_df['Material Name'].dropna()]
            if material_name.strip().lower() in existing_materials:
                return False, f"Material '{material_name}' already exists"
        
        # Add new material
        new_row = [
            material_name.strip(),
            category,
            unit,
            description.strip() if description else "",
            usage.strip() if usage else "",
            "User",
            datetime.now().strftime('%Y-%m-%d')
        ]
        material_worksheet.append_row(new_row)
        
        return True, f"Material '{material_name}' added successfully"
        
    except Exception as e:
        return False, f"Error adding material: {str(e)}"

def add_new_grade(sheets_manager, grade_name, category, description, usage):
    """Add new grade to Grade Master sheet"""
    if not sheets_manager or not grade_name.strip():
        return False, "Invalid input"
    
    try:
        headers = ['Grade/Specification', 'Material Category', 'Description', 'Common Usage', 'Added By', 'Date Added']
        grade_worksheet = sheets_manager.get_or_create_worksheet('Grade Master', headers)
        
        # Check if grade already exists
        grades_df = sheets_manager.dataframe_from_worksheet(grade_worksheet)
        if not grades_df.empty and 'Grade/Specification' in grades_df.columns:
            existing_grades = [str(grade).strip().lower() for grade in grades_df['Grade/Specification'].dropna()]
            if grade_name.strip().lower() in existing_grades:
                return False, f"Grade '{grade_name}' already exists"
        
        # Add new grade
        new_row = [
            grade_name.strip(),
            category.strip() if category else "",
            description.strip() if description else "",
            usage.strip() if usage else "",
            "User",
            datetime.now().strftime('%Y-%m-%d')
        ]
        grade_worksheet.append_row(new_row)
        
        return True, f"Grade '{grade_name}' added successfully"
        
    except Exception as e:
        return False, f"Error adding grade: {str(e)}"

def calculate_days_between_dates(start_date, end_date):
    """Calculate days between two dates"""
    try:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        return (end_date - start_date).days
    except Exception:
        return 0

def format_number_with_commas(number):
    """Format number with commas"""
    try:
        return f"{float(number):,.2f}"
    except (ValueError, TypeError):
        return "0.00"

def get_available_units():
    """Get list of available units for materials"""
    return [
        'Kg', 'Grams', 'Ton', 'Metric Ton', 'Quintal',
        'Liters', 'ML', 'Gallons',
        'Meters', 'CM', 'MM', 'Feet', 'Inches',
        'Sq.Ft', 'Sq.M', 'Sq.CM',
        'CFT', 'Cubic Meters',
        'Nos', 'Pieces', 'Units',
        'Bags', 'Boxes', 'Packets',
        'Rolls', 'Sheets', 'Bundles'
    ]

def get_material_unit_mapping():
    """Get common material unit mappings"""
    return {
        'Cement': 'Bags',
        'Steel': 'Kg',
        'TMT': 'Kg',
        'Rebar': 'Kg',
        'Iron': 'Kg',
        'Bricks': 'Nos',
        'Blocks': 'Nos',
        'Sand': 'CFT',
        'Gravel': 'CFT',
        'Aggregate': 'CFT',
        'Stone': 'CFT',
        'Paint': 'Liters',
        'Primer': 'Liters',
        'Tiles': 'Sq.Ft',
        'Marble': 'Sq.Ft',
        'Granite': 'Sq.Ft',
        'Pipes': 'Meters',
        'Conduit': 'Meters',
        'Wire': 'Meters',
        'Cable': 'Meters',
        'Plywood': 'Sq.Ft',
        'Wood': 'CFT',
        'Lumber': 'CFT'
    }

def suggest_unit_for_material(material):
    """Suggest unit for a material"""
    unit_mapping = get_material_unit_mapping()
    material_lower = material.lower()
    
    for mat, unit in unit_mapping.items():
        if mat.lower() in material_lower:
            return unit
    
    return 'Nos'  # Default unit

def validate_quantity(quantity, material=None):
    """Validate quantity input"""
    try:
        qty = float(quantity)
        if qty <= 0:
            st.error("Quantity must be greater than 0")
            return False
        return True
    except (ValueError, TypeError):
        st.error("Please enter a valid quantity")
        return False

def check_expiry_alert(expiry_date, alert_days=30):
    """Check if item is expiring within alert days"""
    if not expiry_date:
        return False, 0
    
    try:
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        
        current_date = date.today()
        days_to_expire = (expiry_date - current_date).days
        
        return days_to_expire <= alert_days, days_to_expire
    except Exception:
        return False, 0

def create_summary_stats(df, numeric_columns):
    """Create summary statistics for numeric columns"""
    if df.empty:
        return {}
    
    stats = {}
    for col in numeric_columns:
        if col in df.columns:
            try:
                numeric_data = pd.to_numeric(df[col], errors='coerce')
                stats[col] = {
                    'total': numeric_data.sum(),
                    'average': numeric_data.mean(),
                    'min': numeric_data.min(),
                    'max': numeric_data.max(),
                    'count': numeric_data.count()
                }
            except Exception:
                continue
    
    return stats

def highlight_low_stock(val, threshold=10):
    """Highlight low stock values in dataframes"""
    try:
        if float(val) <= 0:
            return 'background-color: #ffcccc'  # Red for out of stock
        elif float(val) <= threshold:
            return 'background-color: #fff3cd'  # Yellow for low stock
        else:
            return ''
    except (ValueError, TypeError):
        return ''
