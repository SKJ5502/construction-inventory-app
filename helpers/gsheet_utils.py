import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

def connect_sheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    gsheet_dict = json.loads(st.secrets["GSHEET_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(gsheet_dict, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name)
