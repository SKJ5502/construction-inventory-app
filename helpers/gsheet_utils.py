import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_sheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("gsheet_auth.json", scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name)