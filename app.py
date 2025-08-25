import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import csv
import os
import logging
from io import BytesIO
import xlsxwriter

# Ρύθμιση logging
logging.basicConfig(
    filename='warehouse_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ρύθμιση σελίδας
st.set_page_config(
    page_title="Σύστημα Διαχείρισης Παραλαβών & Παραγγελιών",
    page_icon="🍊",
    layout="wide"
)

# Τίτλος εφαρμογής
st.title("🍊 Σύστημα Διαχείρισης Παραλαβών & Παραγγελιών")

# Αρχικοποίηση δεδομένων
def init_data():
    """Αρχικοποίηση όλων των δεδομένων"""
    try:
        if not os.path.exists('users.json'):
            users = {
                'admin': {
                    'password': 'admin123',
                    'role': 'admin',
                    'full_name': 'Διαχειριστής Συστήματος'
                }
            }
            with open('users.json', 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            logging.info("Initialized users.json")
        
        if not os.path.exists('storage_locations.json'):
            storage_locations = [
                {"id": 1, "name": "Αποθήκη Α", "capacity": 10000, "description": "Κύρια αποθήκη"},
                {"id": 2, "name": "Αποθήκη Β", "capacity": 5000, "description": "Δευτερεύουσα αποθήκη"}
            ]
            with open('storage_locations.json', 'w', encoding='utf-8') as f:
                json.dump(storage_locations, f, ensure_ascii=False, indent=2)
            logging.info("Initialized storage_locations.json")
    except Exception as e:
        st.error(f"Σφάλμα αρχικοποίησης δεδομένων: {str(e)}")
        logging.error(f"Initialization error: {str(e)}")

# Φόρτωση δεδομένων με caching
@st.cache_data
def load_data():
    """Φόρτωση δεδομένων από αρχεία"""
    data_files = {
        'users': 'users.json',
        'producers': 'producers.json',
        'customers': 'customers.json',
        'agencies': 'agencies.json',
        'receipts': 'receipts.json',
        'orders': 'orders.json',
        'storage_locations': 'storage_locations.json'
    }
    
    data = {}
    for key, filename in data_files.items():
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data[key] = json.load(f)
            else:
                data[key] = {} if key == 'users' else []
            logging.info(f"Loaded {filename}")
        except json.JSONDecodeError as e:
            st.error(f"Σφάλμα φόρτωσης αρχείου {filename}: Μη έγκυρη μορφή JSON")
            logging.error(f"JSON decode error for {filename}: {str(e)}")
            data[key] = {} if key == 'users' else []
        except IOError as e:
            st.error(f"Σφάλμα ανάγνωσης αρχείου {filename}: {str(e)}")
            logging.error(f"IO error for {filename}: {str(e)}")
            data[key] = {} if key == 'users' else []
    
    return data

# Αποθήκευση δεδομένων
def save_data(data):
    """Αποθήκευση δεδομένων σε αρχεία"""
    for key, value in data.items():
        try:
            with open(f'{key}.json', 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {key}.json")
        except IOError as e:
            st.error(f"Σφάλμα αποθήκευσης αρχείου {key}.json: {str(e)}")
            logging.error(f"Save error for {key}.json: {str(e)}")

# Αρχικοποίηση
init_data()
data = load_data()

# Αρχικοποίηση session state
for key, value in data.items():
    if key not in st.session_state:
        st.session_state[key] = value

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'edit_item' not in st.session_state:
    st.session_state.edit_item = None
if 'edit_type' not in st.session_state:
    st.session_state.edit_type = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Κεντρική Βάση"

# Συνάρτηση σύνδεσης
def login():
    st.title("🔐 Σύνδεση στο Σύστημα")
    
    with st.form("login_form"):
        username = st.text_input("Όνομα Χρήστη")
        password = st.text_input("Κωδικός Πρόσβασης", type="password")
        submitted = st.form_submit_button("Σύνδεση")
        
        if submitted:
            if username in st.session_state['users']:
                if password == st.session_state['users'][username]['password']:
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.session_state.user_role = st.session_state['users'][username]['role']
                    st.success("Επιτυχής σύνδεση!")
                    logging.info(f"User {username} logged in successfully")
                    st.rerun()
                else:
                    st.error("Λάθος κωδικός πρόσβασης")
                    logging.warning(f"Failed login attempt for {username}: Incorrect password")
            else:
                st.error("Ο χρήστης δεν υπάρχει")
                logging.warning(f"Failed login attempt: User {username} does not exist")

# Συνάρτηση αποσύνδεσης
def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.edit_item = None
    st.session_state.edit_type = None
    st.success("Αποσυνδεθήκατε επιτυχώς")
    logging.info("User logged out")
    st.rerun()

# Βοηθητικές συναρτήσεις
def get_next_id(items):
    if not items:
        return 1
    return max(item['id'] for item in items) + 1

def can_edit():
    return st.session_state.user_role in ['admin', 'editor']

def can_delete():
    return st.session_state.user_role == 'admin'

def generate_lot_number(receipt_date, producer_id, variety):
    """Αυτόματη δημιουργία αριθμού LOT"""
    date_str = receipt_date.strftime("%y%m%d")
    return f"{date_str}-{producer_id}-{variety[:3].upper()}"

def calculate_storage_usage():
    """Υπολογισμός χρησιμοποιημένου χώρου ανά αποθήκη"""
    storage_usage = {}
    for location in st.session_state['storage_locations']:
        storage_usage[location['id']] = {
            'name': location['name'],
            'capacity': location['capacity'],
            'used': 0,
            'items': []
        }
    
    for receipt in st.session_state['receipts']:
        if 'storage_location_id' in receipt:
            loc_id = receipt['storage_location_id']
            if loc_id in storage_usage:
                storage_usage[loc_id]['used'] += receipt['total_kg']
                storage_usage[loc_id]['items'].append({
                    'id': receipt['id'],
                    'kg': receipt['total_kg'],
                    'date': receipt['receipt_date'],
                    'producer': receipt.get('producer_name', '')
                })
    
    return storage_usage

# Σύνδεση χρήστη
if not st.session_state.authenticated:
    login()
    st.stop()

# Κύρια εφαρμογή
st.sidebar.title(f"👋 Καλώς ήρθατε, {st.session_state.current_user}")
st.sidebar.write(f"**Ρόλος:** {st.session_state.user_role}")

if st.sidebar.button("🚪 Αποσύνδεση"):
    logout()

# Προσθήκη δειγματικών δεδομένων
if not st.session_state['producers']:
    st.session_state['producers'] = [
        {"id": 1, "name": "Παραγωγός Α", "quantity": 1500, "certifications": ["GlobalGAP"]},
        {"id": 2, "name": "Παραγωγός Β", "quantity": 2000, "certifications": ["Βιολογικό"]}
    ]
    save_data({'producers': st.session_state['producers']})
    logging.info("Added sample producers")

if not st.session_state['customers']:
    st.session_state['customers'] = [
        {"id": 1, "name": "Πελάτης Α", "address": "Διεύθυνση 1", "phone": "2101111111"},
        {"id": 2, "name": "Πελάτης Β", "address": "Διεύθυνση 2", "phone": "2102222222"}
    ]
    save_data({'customers': st.session_state['customers']})
    logging.info("Added sample customers")

# Πλαϊνό μενού