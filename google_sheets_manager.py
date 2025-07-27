import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
import json
from datetime import datetime, date
import streamlit as st

class GoogleSheetsManager:
    def __init__(self):
        self.spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID", "1ndk1u8dXgYvELIRDt0ZDtfzlUluW4Y8KGXUsE4ExwRw")
        self.credentials = None
        self.client = None
        self.spreadsheet = None
        self.initialize_connection()
    
    def initialize_connection(self):
        """Initialize Google Sheets connection"""
        try:
            # Get credentials from environment variables
            creds_json = os.getenv("GOOGLE_CREDENTIALS", "{}")
            if creds_json == "{}":
                print("Google Sheets credentials not found. Please set GOOGLE_CREDENTIALS environment variable.")
                return False
            
            creds_dict = json.loads(creds_json)
            
            # Define the scope
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Create credentials
            self.credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
            self.client = gspread.authorize(self.credentials)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            print(f"✅ Successfully connected to Google Sheets: {self.spreadsheet.title}")
            return True
        except Exception as e:
            print(f"Failed to connect to Google Sheets: {str(e)}")
            return False
    
    def get_or_create_worksheet(self, sheet_name, headers):
        """Get existing worksheet or create new one with headers"""
        if not self.spreadsheet:
            raise Exception("Not connected to Google Sheets")
            
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            print(f"Found existing worksheet: {sheet_name}")
            
            # Check if headers match, if not, update them
            try:
                existing_headers = worksheet.row_values(1)
                print(f"Existing headers: {existing_headers}")
                print(f"Required headers: {headers}")
                if existing_headers != headers:
                    print(f"Updating headers for {sheet_name}")
                    # Clear first row and add new headers
                    worksheet.delete_rows(1)
                    worksheet.insert_row(headers, 1)
                    print(f"Headers updated: {headers}")
                else:
                    print(f"Headers already match for {sheet_name}")
            except Exception as e:
                print(f"Error checking/updating headers: {e}")
                
        except gspread.WorksheetNotFound:
            print(f"Creating new worksheet: {sheet_name}")
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
            worksheet.append_row(headers)
            print(f"Added headers to new worksheet: {headers}")
        return worksheet
    
    def dataframe_from_worksheet(self, worksheet):
        """Convert worksheet to pandas DataFrame"""
        try:
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()
    
    # Vendor Management
    def get_vendors(self):
        """Get all vendors"""
        try:
            headers = ['Vendor Name', 'Material Supplied', 'Contact Person', 'Phone', 'Email', 'Address']
            worksheet = self.get_or_create_worksheet('Vendor Master', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching vendors: {str(e)}")
            return pd.DataFrame()
    
    def add_vendor(self, vendor_data):
        """Add new vendor"""
        try:
            headers = ['Vendor Name', 'Material Supplied', 'Contact Person', 'Phone', 'Email', 'Address']
            worksheet = self.get_or_create_worksheet('Vendor Master', headers)
            row = [vendor_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding vendor: {str(e)}")
            return False
    
    def delete_vendor(self, vendor_name):
        """Delete vendor by name"""
        try:
            headers = ['Vendor Name', 'Material Supplied', 'Contact Person', 'Phone', 'Email', 'Address']
            worksheet = self.get_or_create_worksheet('Vendor Master', headers)
            vendors = worksheet.get_all_records()
            for i, vendor in enumerate(vendors, start=2):
                if vendor['Vendor Name'] == vendor_name:
                    worksheet.delete_rows(i)
                    return True
            return False
        except Exception as e:
            st.error(f"Error deleting vendor: {str(e)}")
            return False
    
    # Material Master
    def get_material_master(self):
        """Get all materials from master"""
        try:
            headers = ['Material Name', 'Category', 'Unit', 'Reorder Level', 'Has Expiry', 'Shelf Life (Months)', 'Description', 'Added By', 'Date Added']
            worksheet = self.get_or_create_worksheet('Material Master', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching materials: {str(e)}")
            return pd.DataFrame()
    
    def add_material_master(self, material_data):
        """Add new material to master"""
        try:
            headers = ['Material Name', 'Category', 'Unit', 'Reorder Level', 'Has Expiry', 'Shelf Life (Months)', 'Description', 'Added By', 'Date Added']
            worksheet = self.get_or_create_worksheet('Material Master', headers)
            row = [material_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding material: {str(e)}")
            return False
    
    # Inward Register
    def get_inward_entries(self):
        """Get all inward entries"""
        try:
            headers = ['Date', 'Material', 'Vendor Name', 'Quantity', 'Unit', 'Rate per Unit', 'Amount', 'Invoice Number', 'Received By', 'Remarks', 'Expiry Date']
            worksheet = self.get_or_create_worksheet('Inward Register', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching inward entries: {str(e)}")
            return pd.DataFrame()
    
    def add_inward_entry(self, inward_data):
        """Add new inward entry"""
        try:
            headers = ['Date', 'Material', 'Vendor Name', 'Quantity', 'Unit', 'Rate per Unit', 'Amount', 'Invoice Number', 'Received By', 'Remarks', 'Expiry Date']
            worksheet = self.get_or_create_worksheet('Inward Register', headers)
            row = [inward_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding inward entry: {str(e)}")
            return False
    
    # Outward Register
    def get_outward_entries(self):
        """Get all outward entries"""
        try:
            headers = ['Date', 'Material', 'Quantity', 'Unit', 'Issued To', 'Purpose', 'Remarks']
            worksheet = self.get_or_create_worksheet('Outward Register', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching outward entries: {str(e)}")
            return pd.DataFrame()
    
    def add_outward_entry(self, outward_data):
        """Add new outward entry"""
        try:
            headers = ['Date', 'Material', 'Quantity', 'Unit', 'Issued To', 'Purpose', 'Remarks']
            worksheet = self.get_or_create_worksheet('Outward Register', headers)
            row = [outward_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding outward entry: {str(e)}")
            return False
    
    # Returns Register
    def get_return_entries(self):
        """Get all return entries"""
        try:
            headers = ['Date', 'Material', 'Returned By', 'Quantity', 'Unit', 'Reason', 'Remarks']
            worksheet = self.get_or_create_worksheet('Returns Register', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching return entries: {str(e)}")
            return pd.DataFrame()
    
    def add_return_entry(self, return_data):
        """Add new return entry"""
        try:
            headers = ['Date', 'Material', 'Returned By', 'Quantity', 'Unit', 'Reason', 'Remarks']
            worksheet = self.get_or_create_worksheet('Returns Register', headers)
            row = [return_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding return entry: {str(e)}")
            return False
    
    # Damage/Loss Register
    def get_damage_entries(self):
        """Get all damage/loss entries"""
        try:
            headers = ['Date', 'Material', 'Quantity Lost/Damaged', 'Reason', 'Reported By', 'Remarks']
            worksheet = self.get_or_create_worksheet('Damage Loss Register', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching damage entries: {str(e)}")
            return pd.DataFrame()
    
    def add_damage_entry(self, damage_data):
        """Add new damage entry"""
        try:
            headers = ['Date', 'Material', 'Quantity Lost/Damaged', 'Reason', 'Reported By', 'Remarks']
            worksheet = self.get_or_create_worksheet('Damage Loss Register', headers)
            row = [damage_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding damage entry: {str(e)}")
            return False
    
    # Stock Reconciliation
    def calculate_reconciliation(self):
        """Calculate stock reconciliation"""
        try:
            inward_df = self.get_inward_entries()
            outward_df = self.get_outward_entries()
            returns_df = self.get_return_entries()
            damage_df = self.get_damage_entries()
            
            # Get unique materials
            materials = set()
            if not inward_df.empty:
                materials.update(inward_df['Material'].unique())
            if not outward_df.empty:
                materials.update(outward_df['Material'].unique())
            
            reconciliation_data = []
            
            for material in materials:
                # Calculate totals
                total_inward = inward_df[inward_df['Material'] == material]['Quantity'].astype(float).sum() if not inward_df.empty else 0
                total_outward = outward_df[outward_df['Material'] == material]['Quantity'].astype(float).sum() if not outward_df.empty else 0
                total_returns = returns_df[returns_df['Material'] == material]['Quantity'].astype(float).sum() if not returns_df.empty else 0
                total_loss = damage_df[damage_df['Material'] == material]['Quantity Lost/Damaged'].astype(float).sum() if not damage_df.empty else 0
                
                current_stock = total_inward + total_returns - total_outward - total_loss
                
                reconciliation_data.append({
                    'Material': material,
                    'Total Inward': total_inward,
                    'Total Outward': total_outward,
                    'Total Returns': total_returns,
                    'Total Loss': total_loss,
                    'Current Stock': current_stock
                })
            
            reconciliation_df = pd.DataFrame(reconciliation_data)
            
            # Save to Google Sheets
            if not reconciliation_df.empty:
                headers = ['Material', 'Total Inward', 'Total Outward', 'Total Returns', 'Total Loss', 'Current Stock']
                worksheet = self.get_or_create_worksheet('Reconciliation', headers)
                worksheet.clear()
                worksheet.append_row(headers)
                for _, row in reconciliation_df.iterrows():
                    worksheet.append_row(row.tolist())
            
            return reconciliation_df
            
        except Exception as e:
            st.error(f"Error calculating reconciliation: {str(e)}")
            return pd.DataFrame()
    
    # Daily Closing
    def generate_daily_closing(self, closing_date):
        """Generate daily closing report"""
        try:
            # Get data for the specific date
            date_str = closing_date.strftime('%Y-%m-%d')
            
            inward_df = self.get_inward_entries()
            outward_df = self.get_outward_entries()
            returns_df = self.get_return_entries()
            damage_df = self.get_damage_entries()
            
            # Filter by date
            inward_today = inward_df[inward_df['Date'] == date_str] if not inward_df.empty else pd.DataFrame()
            outward_today = outward_df[outward_df['Date'] == date_str] if not outward_df.empty else pd.DataFrame()
            returns_today = returns_df[returns_df['Date'] == date_str] if not returns_df.empty else pd.DataFrame()
            damage_today = damage_df[damage_df['Date'] == date_str] if not damage_df.empty else pd.DataFrame()
            
            # Get current reconciliation
            reconciliation_df = self.calculate_reconciliation()
            
            daily_closing_data = []
            
            if not reconciliation_df.empty:
                for _, row in reconciliation_df.iterrows():
                    material = row['Material']
                    current_stock = row['Current Stock']
                    
                    received = inward_today[inward_today['Material'] == material]['Quantity'].astype(float).sum() if not inward_today.empty else 0
                    issued = outward_today[outward_today['Material'] == material]['Quantity'].astype(float).sum() if not outward_today.empty else 0
                    returned = returns_today[returns_today['Material'] == material]['Quantity'].astype(float).sum() if not returns_today.empty else 0
                    losses = damage_today[damage_today['Material'] == material]['Quantity Lost/Damaged'].astype(float).sum() if not damage_today.empty else 0
                    
                    opening_stock = current_stock - received - returned + issued + losses
                    closing_stock = current_stock
                    
                    daily_closing_data.append({
                        'Date': date_str,
                        'Material': material,
                        'Opening Stock': opening_stock,
                        'Received': received,
                        'Issued': issued,
                        'Returns': returned,
                        'Losses': losses,
                        'Closing Stock': closing_stock
                    })
            
            return pd.DataFrame(daily_closing_data)
            
        except Exception as e:
            st.error(f"Error generating daily closing: {str(e)}")
            return pd.DataFrame()
    
    def save_daily_closing(self, daily_closing_df, closing_date):
        """Save daily closing to Google Sheets"""
        try:
            headers = ['Date', 'Material', 'Opening Stock', 'Received', 'Issued', 'Returns', 'Losses', 'Closing Stock']
            worksheet = self.get_or_create_worksheet('Daily Closing', headers)
            
            # Remove existing entries for the date
            date_str = closing_date.strftime('%Y-%m-%d')
            existing_data = worksheet.get_all_records()
            rows_to_delete = []
            for i, record in enumerate(existing_data, start=2):
                if record.get('Date') == date_str:
                    rows_to_delete.append(i)
            
            # Delete in reverse order to maintain row indices
            for row_idx in reversed(rows_to_delete):
                worksheet.delete_rows(row_idx)
            
            # Add new entries
            for _, row in daily_closing_df.iterrows():
                worksheet.append_row(row.tolist())
            
            return True
        except Exception as e:
            st.error(f"Error saving daily closing: {str(e)}")
            return False
    
    # Stock Summary
    def get_stock_summary(self):
        """Get stock summary"""
        try:
            reconciliation_df = self.calculate_reconciliation()
            if not reconciliation_df.empty:
                stock_summary = reconciliation_df[['Material', 'Current Stock']].copy()
                stock_summary['Unit'] = 'Nos'  # Default unit
                stock_summary['Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return stock_summary
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error getting stock summary: {str(e)}")
            return pd.DataFrame()
    
    # BOQ Mapping
    def get_boq_mappings(self):
        """Get all BOQ mappings"""
        try:
            headers = ['BOQ Item', 'Description', 'Material', 'Quantity Allocated', 'Unit', 'Remarks']
            worksheet = self.get_or_create_worksheet('BOQ Mapping', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching BOQ mappings: {str(e)}")
            return pd.DataFrame()
    
    def add_boq_mapping(self, boq_data):
        """Add new BOQ mapping"""
        try:
            headers = ['BOQ Item', 'Description', 'Material', 'Quantity Allocated', 'Unit', 'Remarks']
            worksheet = self.get_or_create_worksheet('BOQ Mapping', headers)
            row = [boq_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding BOQ mapping: {str(e)}")
            return False
    
    # Indent Register
    def get_indents(self):
        """Get all indents"""
        try:
            headers = ['Date', 'Material', 'Quantity Indented', 'Purpose', 'Requested By', 'Status']
            worksheet = self.get_or_create_worksheet('Indent Register', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching indents: {str(e)}")
            return pd.DataFrame()
    
    def add_indent(self, indent_data):
        """Add new indent"""
        try:
            headers = ['Date', 'Material', 'Quantity Indented', 'Purpose', 'Requested By', 'Status']
            worksheet = self.get_or_create_worksheet('Indent Register', headers)
            row = [indent_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding indent: {str(e)}")
            return False
    
    # Material Transfer Register
    def get_transfers(self):
        """Get all transfers"""
        try:
            headers = ['Date', 'From Location', 'To Location', 'Material', 'Quantity', 'Unit', 'Remarks']
            worksheet = self.get_or_create_worksheet('Material Transfer Register', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching transfers: {str(e)}")
            return pd.DataFrame()
    
    def add_transfer(self, transfer_data):
        """Add new transfer"""
        try:
            headers = ['Date', 'From Location', 'To Location', 'Material', 'Quantity', 'Unit', 'Remarks']
            worksheet = self.get_or_create_worksheet('Material Transfer Register', headers)
            row = [transfer_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding transfer: {str(e)}")
            return False
    
    # Scrap Register
    def get_scrap_entries(self):
        """Get all scrap entries"""
        try:
            headers = ['Date', 'Scrap Item', 'Material Source', 'Quantity', 'Scrap Value', 'Sold/Stored']
            worksheet = self.get_or_create_worksheet('Scrap Register', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching scrap entries: {str(e)}")
            return pd.DataFrame()
    
    def add_scrap_entry(self, scrap_data):
        """Add new scrap entry"""
        try:
            headers = ['Date', 'Scrap Item', 'Material Source', 'Quantity', 'Scrap Value', 'Sold/Stored']
            worksheet = self.get_or_create_worksheet('Scrap Register', headers)
            row = [scrap_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding scrap entry: {str(e)}")
            return False
    
    # Rate Contract Register
    def get_rate_contracts(self):
        """Get all rate contracts"""
        try:
            headers = ['Material', 'Vendor', 'Agreed Rate', 'Validity Period', 'Contract Ref No', 'Remarks']
            worksheet = self.get_or_create_worksheet('Rate Contract Register', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching rate contracts: {str(e)}")
            return pd.DataFrame()
    
    def add_rate_contract(self, contract_data):
        """Add new rate contract"""
        try:
            headers = ['Material', 'Vendor', 'Agreed Rate', 'Validity Period', 'Contract Ref No', 'Remarks']
            worksheet = self.get_or_create_worksheet('Rate Contract Register', headers)
            row = [contract_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding rate contract: {str(e)}")
            return False
    
    # PO Register
    def get_purchase_orders(self):
        """Get all purchase orders"""
        try:
            headers = ['PO Number', 'Date', 'Vendor', 'Material', 'Quantity', 'Rate', 'Amount', 'Status', 'Remarks']
            worksheet = self.get_or_create_worksheet('PO Register', headers)
            return self.dataframe_from_worksheet(worksheet)
        except Exception as e:
            st.error(f"Error fetching purchase orders: {str(e)}")
            return pd.DataFrame()
    
    def add_purchase_order(self, po_data):
        """Add new purchase order"""
        try:
            headers = ['PO Number', 'Date', 'Vendor', 'Material', 'Quantity', 'Rate', 'Amount', 'Status', 'Remarks']
            worksheet = self.get_or_create_worksheet('PO Register', headers)
            row = [po_data.get(header, '') for header in headers]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error adding purchase order: {str(e)}")
            return False
    
    # Reports
    def generate_daily_summary_report(self, start_date, end_date):
        """Generate daily summary report"""
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            inward_df = self.get_inward_entries()
            outward_df = self.get_outward_entries()
            
            if not inward_df.empty:
                inward_filtered = inward_df[(inward_df['Date'] >= start_str) & (inward_df['Date'] <= end_str)]
                inward_summary = inward_filtered.groupby('Date').agg({
                    'Quantity': 'sum',
                    'Amount': 'sum'
                }).reset_index()
                inward_summary.columns = ['Date', 'Total Inward Qty', 'Total Inward Value']
            else:
                inward_summary = pd.DataFrame()
            
            if not outward_df.empty:
                outward_filtered = outward_df[(outward_df['Date'] >= start_str) & (outward_df['Date'] <= end_str)]
                outward_summary = outward_filtered.groupby('Date').agg({
                    'Quantity': 'sum'
                }).reset_index()
                outward_summary.columns = ['Date', 'Total Outward Qty']
            else:
                outward_summary = pd.DataFrame()
            
            # Merge summaries
            if not inward_summary.empty and not outward_summary.empty:
                summary = pd.merge(inward_summary, outward_summary, on='Date', how='outer')
            elif not inward_summary.empty:
                summary = inward_summary
            elif not outward_summary.empty:
                summary = outward_summary
            else:
                summary = pd.DataFrame()
            
            return summary.fillna(0) if not summary.empty else pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error generating daily summary report: {str(e)}")
            return pd.DataFrame()
    
    def generate_monthly_summary_report(self, start_date, end_date):
        """Generate monthly summary report"""
        try:
            daily_summary = self.generate_daily_summary_report(start_date, end_date)
            if not daily_summary.empty:
                daily_summary['Date'] = pd.to_datetime(daily_summary['Date'])
                daily_summary['Month'] = daily_summary['Date'].dt.to_period('M')
                
                monthly_summary = daily_summary.groupby('Month').agg({
                    'Total Inward Qty': 'sum',
                    'Total Inward Value': 'sum',
                    'Total Outward Qty': 'sum'
                }).reset_index()
                
                return monthly_summary
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error generating monthly summary report: {str(e)}")
            return pd.DataFrame()
    
    def generate_vendor_analysis_report(self):
        """Generate vendor analysis report"""
        try:
            inward_df = self.get_inward_entries()
            if not inward_df.empty:
                vendor_analysis = inward_df.groupby('Vendor Name').agg({
                    'Amount': ['sum', 'mean'],
                    'Quantity': 'sum'
                }).reset_index()
                
                vendor_analysis.columns = ['Vendor Name', 'Total Purchase Value', 'Average Rate', 'Total Quantity']
                vendor_analysis = vendor_analysis.sort_values('Total Purchase Value', ascending=False)
                
                return vendor_analysis
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error generating vendor analysis report: {str(e)}")
            return pd.DataFrame()
    
    def generate_material_analysis_report(self):
        """Generate material analysis report"""
        try:
            inward_df = self.get_inward_entries()
            if not inward_df.empty:
                material_analysis = inward_df.groupby('Material').agg({
                    'Amount': ['sum', 'mean'],
                    'Quantity': 'sum',
                    'Vendor Name': 'nunique'
                }).reset_index()
                
                material_analysis.columns = ['Material', 'Total Purchase Value', 'Average Rate', 'Total Quantity', 'Number of Vendors']
                material_analysis = material_analysis.sort_values('Total Purchase Value', ascending=False)
                
                return material_analysis
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error generating material analysis report: {str(e)}")
            return pd.DataFrame()
    
    def generate_expiry_report(self):
        """Generate expiry report"""
        try:
            inward_df = self.get_inward_entries()
            if not inward_df.empty and 'Expiry Date' in inward_df.columns:
                current_date = datetime.now().date()
                
                # Filter items with expiry dates
                expiry_df = inward_df[inward_df['Expiry Date'].notna() & (inward_df['Expiry Date'] != '')]
                
                if not expiry_df.empty:
                    expiry_df['Expiry Date'] = pd.to_datetime(expiry_df['Expiry Date']).dt.date
                    expiry_df['Days to Expire'] = (expiry_df['Expiry Date'] - current_date).dt.days
                    
                    # Items expiring within 30 days
                    expiring_soon = expiry_df[expiry_df['Days to Expire'] <= 30]
                    
                    return expiring_soon[['Material', 'Vendor Name', 'Quantity', 'Expiry Date', 'Days to Expire']]
            
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error generating expiry report: {str(e)}")
            return pd.DataFrame()
    
    def get_dashboard_metrics(self):
        """Get dashboard metrics"""
        try:
            metrics = {}
            
            # Total purchase value
            inward_df = self.get_inward_entries()
            if not inward_df.empty:
                metrics['total_purchase'] = inward_df['Amount'].astype(float).sum()
                metrics['total_materials'] = inward_df['Material'].nunique()
            else:
                metrics['total_purchase'] = 0
                metrics['total_materials'] = 0
            
            # Active vendors
            vendors_df = self.get_vendors()
            metrics['active_vendors'] = len(vendors_df) if not vendors_df.empty else 0
            
            # Pending indents
            indents_df = self.get_indents()
            if not indents_df.empty:
                metrics['pending_indents'] = len(indents_df[indents_df['Status'] == 'Pending'])
            else:
                metrics['pending_indents'] = 0
            
            return metrics
        except Exception as e:
            st.error(f"Error getting dashboard metrics: {str(e)}")
            return {}
