import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import csv
import os
import bcrypt
import logging
from io import BytesIO
import xlsxwriter  # Requires pip install xlsxwriter

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

# Συναρτήσεις ασφαλείας
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def init_data():
    """Αρχικοποίηση όλων των δεδομένων"""
    try:
        if not os.path.exists('users.json'):
            users = {
                'admin': {
                    'password': hash_password('admin123'),
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

# Συναρτήσεις φόρτωσης και αποθήκευσης με caching
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
                if check_password(password, st.session_state['users'][username]['password']):
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.session_state.user_role = st.session_state['users'][username]['role']
                    st.success("Επιτυχής σύνδεση!")
                    logging.info(f"User {username} logged in successfully")
                    time.sleep(1)
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
    time.sleep(1)
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

# Πλαϊνό μενού για γρήγορη πρόσβαση
st.sidebar.header("📋 Γρήγορη Πρόσβαση")
menu_options = [
    "Κεντρική Βάση", 
    "Νέα Παραλαβή", 
    "Νέα Παραγγελία", 
    "Αναφορές", 
    "Διαχείριση"
]
if st.session_state.user_role == 'admin':
    menu_options.extend(["Διαχείριση Χρηστών", "Αποθηκευτικοί Χώροι"])

selected_menu = st.sidebar.selectbox("Επιλέξτε ενότητα", menu_options, 
                                    index=menu_options.index(st.session_state.current_tab))

# Ενημέρωση του τρέχοντος tab
st.session_state.current_tab = selected_menu

# Στήλες για το tab layout
tabs = st.tabs(menu_options)

# Συνάρτηση καθαρισμού session state
def clear_form_state(prefix):
    """Καθαρισμός session state κλειδιών που σχετίζονται με φόρμες"""
    for key in list(st.session_state.keys()):
        if key.startswith(prefix):
            del st.session_state[key]

# Συνάρτηση εξαγωγής σε Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=True, sheet_name='Sheet1')
    return output.getvalue()

# Tab 1: Κεντρική Βάση
def show_central_database():
    with tabs[0]:
        st.header("📊 Κεντρική Βάση Δεδομένων")
        
        data_type = st.selectbox("Επιλέξτε τύπο δεδομένων", ["Παραλαβές", "Παραγγελίες", "Παραγωγοί", "Πελάτες"])
        
        if data_type == "Παραλαβές":
            items = st.session_state['receipts']
            item_key = 'receipts'
            columns = ['id', 'receipt_date', 'producer_name', 'total_kg', 'total_value', 'lot', 'storage_location']
        elif data_type == "Παραγγελίες":
            items = st.session_state['orders']
            item_key = 'orders'
            columns = ['id', 'date', 'customer', 'total_kg', 'total_value', 'executed_quantity', 'lot']
        elif data_type == "Παραγωγοί":
            items = st.session_state['producers']
            item_key = 'producers'
            columns = ['id', 'name', 'quantity', 'certifications']
        else:
            items = st.session_state['customers']
            item_key = 'customers'
            columns = ['id', 'name', 'address', 'phone']
        
        if items:
            df = pd.DataFrame(items)
            if not df.empty:
                display_columns = [col for col in columns if col in df.columns]
                st.dataframe(df[display_columns], use_container_width=True)
                
                options = [f"{item['id']} - {item.get('producer_name', item.get('name', item.get('customer', '')))}" for item in items]
                selected_option = st.selectbox("Επιλέξτε εγγραφή για διαχείριση", options)
                
                if selected_option:
                    selected_id = int(selected_option.split(" - ")[0])
                    selected_item = next((item for item in items if item['id'] == selected_id), None)
                    
                    if selected_item:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Λεπτομέρειες Εγγραφής:**")
                            st.json(selected_item)
                        
                        with col2:
                            st.write("**Ενέργειες:**")
                            
                            if can_edit() and st.button("✏️ Επεξεργασία"):
                                st.session_state.edit_item = selected_item
                                st.session_state.edit_type = item_key
                                st.session_state.current_tab = "Νέα Παραλαβή" if item_key == 'receipts' else "Νέα Παραγγελία"
                                st.rerun()
                            
                            if can_delete() and st.button("🗑️ Διαγραφή"):
                                st.session_state[item_key] = [item for item in items if item['id'] != selected_id]
                                save_data({item_key: st.session_state[item_key]})
                                st.success(f"✅ Διαγραφή εγγραφής #{selected_id} επιτυχής!")
                                logging.info(f"Deleted {item_key} #{selected_id} by {st.session_state.current_user}")
                                time.sleep(1)
                                st.rerun()
            else:
                st.info(f"Δεν υπάρχουν καταχωρημένες {data_type}")
        else:
            st.info(f"Δεν υπάρχουν καταχωρημένες {data_type}")

# Tab 2: Νέα Παραλαβή
def show_new_receipt():
    with tabs[1]:
        if not can_edit():
            st.warning("⛔ Δεν έχετε δικαιώματα για καταχώρηση/επεξεργασία παραλαβών")
            return
        
        if st.session_state.edit_item and st.session_state.edit_type == 'receipts':
            receipt = st.session_state.edit_item
            is_edit = True
            st.header("📝 Επεξεργασία Παραλαβής")
        else:
            receipt = {}
            is_edit = False
            st.header("📥 Καταχώρηση Νέας Παραλαβής")
        
        with st.form("receipt_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if is_edit:
                    receipt_id = st.number_input("Αριθμός Παραλαβής", value=receipt['id'], disabled=True)
                    st.text_input("Αριθμός LOT", value=receipt.get('lot', ''), disabled=True)
                else:
                    receipt_id = st.number_input("Αριθμός Παραλαβής", min_value=1, step=1, value=get_next_id(st.session_state['receipts']))
                
                try:
                    receipt_date = datetime.strptime(receipt['receipt_date'], '%Y-%m-%d') if is_edit else datetime.today()
                except (ValueError, KeyError):
                    st.error("❌ Μη έγκυρη μορφή ημερομηνίας")
                    receipt_date = datetime.today()
                receipt_date = st.date_input("Ημερομηνία Παραλαβής", value=receipt_date)
                
                producer_options = [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
                default_index = 0
                if is_edit and 'producer_id' in receipt:
                    default_index = next((i for i, p in enumerate(producer_options) if str(receipt['producer_id']) in p), 0)
                selected_producer = st.selectbox("Παραγωγός", options=producer_options, index=default_index)
                producer_id = int(selected_producer.split(" - ")[0]) if selected_producer else None
                producer_name = selected_producer.split(" - ")[1] if selected_producer else ""
                
                variety = st.text_input("Ποικιλία", value=receipt.get('variety', ''))
                
                if variety and producer_id and receipt_date:
                    lot_number = generate_lot_number(receipt_date, producer_id, variety)
                    if not is_edit:
                        st.text_input("Αριθμός LOT", value=lot_number, disabled=True)
                else:
                    lot_number = receipt.get('lot', '')
                
                storage_options = [f"{s['id']} - {s['name']}" for s in st.session_state['storage_locations']]
                default_storage_index = 0
                if is_edit and 'storage_location_id' in receipt:
                    default_storage_index = next((i for i, s in enumerate(storage_options) if str(receipt['storage_location_id']) in s), 0)
                selected_storage = st.selectbox("Αποθηκευτικός Χώρος", options=storage_options, index=default_storage_index)
                storage_id = int(selected_storage.split(" - ")[0]) if selected_storage else None
                
                paid_options = ["Ναι", "Όχι"]
                paid_index = 0 if receipt.get('paid') == "Ναι" else 1
                paid_status = st.selectbox("Πληρώθηκε;", paid_options, index=paid_index)
                
                invoice_ref = st.text_input("Σχετικό Τιμολόγιο", value=receipt.get('invoice_ref', ''))
            
            with col2:
                st.subheader("📊 Ποσότητες ανά Νούμερο")
                sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα", "Σκάρτα", "Μεταποίηση"]
                size_quantities = receipt.get('size_quantities', {})
                for size in sizes:
                    size_quantities[size] = st.number_input(
                        f"Ποσότητα για νούμερο {size}", 
                        min_value=0, max_value=100000, step=1, 
                        value=int(size_quantities.get(size, 0)),
                        key=f"size_{size}_{receipt_id if is_edit else 'new'}"
                    )
                
                st.subheader("📊 Ποσότητες ανά Ποιότητα")
                qualities = ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Διάφορα", "Μεταποίηση"]
                quality_quantities = receipt.get('quality_quantities', {})
                for quality in qualities:
                    quality_quantities[quality] = st.number_input(
                        f"Ποσότητα για ποιότητα {quality}", 
                        min_value=0, max_value=100000, step=1, 
                        value=int(quality_quantities.get(quality, 0)),
                        key=f"quality_{quality}_{receipt_id if is_edit else 'new'}"
                    )
                
                certifications = st.multiselect(
                    "📑 Πιστοποιήσεις",
                    ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"],
                    default=receipt.get('certifications', [])
                )
                
                agreed_price_per_kg = st.number_input(
                    "💰 Συμφωνηθείσα Τιμή ανά κιλό", 
                    min_value=0.0, max_value=100.0, step=0.01, 
                    value=receipt.get('agreed_price_per_kg', 0.0)
                )
                
                total_kg = sum(size_quantities.values()) + sum(quality_quantities.values())
                total_value = total_kg * agreed_price_per_kg if agreed_price_per_kg else 0
                
                if total_kg > 0:
                    st.info(f"📦 Σύνολο κιλών: {total_kg} kg")
                    st.success(f"💶 Συνολική αξία: {total_value:.2f} €")
                
                observations = st.text_area("📝 Παρατηρήσεις", value=receipt.get('observations', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("✅ Καταχώρηση Παραλαβής")
            with col2:
                if is_edit:
                    if st.form_submit_button("❌ Ακύρωση Επεξεργασίας"):
                        st.session_state.edit_item = None
                        st.session_state.edit_type = None
                        clear_form_state(f"size_")
                        clear_form_state(f"quality_")
                        st.rerun()
            
            if submitted:
                with st.spinner("Καταχώρηση σε εξέλιξη..."):
                    if not producer_name:
                        st.error("❌ Παρακαλώ επιλέξτε παραγωγό")
                    elif not variety:
                        st.error("❌ Παρακαλώ συμπληρώστε την ποικιλία")
                    elif not storage_id:
                        st.error("❌ Παρακαλώ επιλέξτε αποθηκευτικό χώρο")
                    elif total_kg <= 0:
                        st.error("❌ Η συνολική ποσότητα πρέπει να είναι μεγαλύτερη από 0")
                    else:
                        new_receipt = {
                            "id": receipt_id,
                            "receipt_date": receipt_date.strftime("%Y-%m-%d"),
                            "producer_id": producer_id,
                            "producer_name": producer_name,
                            "variety": variety,
                            "lot": lot_number,
                            "storage_location_id": storage_id,
                            "storage_location": selected_storage.split(" - ")[1] if selected_storage else "",
                            "size_quantities": size_quantities,
                            "quality_quantities": quality_quantities,
                            "certifications": certifications,
                            "agreed_price_per_kg": agreed_price_per_kg,
                            "total_kg": total_kg,
                            "total_value": total_value,
                            "paid": paid_status,
                            "invoice_ref": invoice_ref,
                            "observations": observations,
                            "created_by": st.session_state.current_user,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        if is_edit:
                            for i, item in enumerate(st.session_state['receipts']):
                                if item['id'] == receipt_id:
                                    st.session_state['receipts'][i] = new_receipt
                                    break
                            st.success(f"✅ Η παραλαβή #{receipt_id} ενημερώθηκε επιτυχώς!")
                            logging.info(f"Receipt #{receipt_id} updated by {st.session_state.current_user}")
                        else:
                            st.session_state['receipts'].append(new_receipt)
                            st.success(f"✅ Η παραλαβή #{receipt_id} καταχωρήθηκε επιτυχώς!")
                            logging.info(f"Receipt #{receipt_id} added by {st.session_state.current_user}")
                        
                        save_data({'receipts': st.session_state['receipts']})
                        st.session_state.edit_item = None
                        st.session_state.edit_type = None
                        clear_form_state(f"size_")
                        clear_form_state(f"quality_")

# Tab 3: Νέα Παραγγελία
def show_new_order():
    with tabs[2]:
        if not can_edit():
            st.warning("⛔ Δεν έχετε δικαιώματα για καταχώρηση/επεξεργασία παραγγελιών")
            return
        
        if st.session_state.edit_item and st.session_state.edit_type == 'orders':
            order = st.session_state.edit_item
            is_edit = True
            st.header("📝 Επεξεργασία Παραγγελίας")
        else:
            order = {}
            is_edit = False
            st.header("📋 Καταχώρηση Νέας Παραγγελίας")
        
        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if is_edit:
                    order_id = st.number_input("Αριθμός Παραγγελίας", value=order['id'], disabled=True)
                    st.text_input("Αριθμός LOT", value=order.get('lot', ''), disabled=True)
                else:
                    order_id = st.number_input("Αριθμός Παραγγελίας", min_value=1, step=1, value=get_next_id(st.session_state['orders']))
                
                try:
                    order_date = datetime.strptime(order['date'], '%Y-%m-%d') if is_edit else datetime.today()
                except (ValueError, KeyError):
                    st.error("❌ Μη έγκυρη μορφή ημερομηνίας")
                    order_date = datetime.today()
                order_date = st.date_input("Ημερομηνία Παραγγελίας", value=order_date)
                
                customer_options = [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
                default_customer_index = 0
                if is_edit and 'customer_id' in order:
                    default_customer_index = next((i for i, c in enumerate(customer_options) if str(order['customer_id']) in c), 0)
                selected_customer = st.selectbox("Πελάτης", options=customer_options, index=default_customer_index)
                customer_id = int(selected_customer.split(" - ")[0]) if selected_customer else None
                customer_name = selected_customer.split(" - ")[1] if selected_customer else ""
                
                variety = st.text_input("Ποικιλία Παραγγελίας", value=order.get('variety', ''))
                
                if variety and customer_id and order_date:
                    lot_number = generate_lot_number(order_date, customer_id, variety)
                    if not is_edit:
                        st.text_input("Αριθμός LOT", value=lot_number, disabled=True)
                else:
                    lot_number = order.get('lot', '')
                
                paid_options = ["Ναι", "Όχι"]
                paid_index = 0 if order.get('paid') == "Ναι" else 1
                paid_status = st.selectbox("Πληρώθηκε;", paid_options, index=paid_index)
                
                invoice_ref = st.text_input("Σχετικό Τιμολόγιο", value=order.get('invoice_ref', ''))
            
            with col2:
                st.subheader("📦 Ποσότητες Παραγγελίας ανά Νούμερο")
                sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα", "Σκάρτα", "Μεταποίηση"]
                order_size_quantities = order.get('size_quantities', {})
                for size in sizes:
                    order_size_quantities[size] = st.number_input(
                        f"Ποσότητα για νούμερο {size}", 
                        min_value=0, max_value=100000, step=1, 
                        value=int(order_size_quantities.get(size, 0)),
                        key=f"order_size_{size}_{order_id if is_edit else 'new'}"
                    )
                
                st.subheader("📦 Ποσότητες Παραγγελίας ανά Ποιότητα")
                qualities = ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Διάφορα", "Μεταποίηση"]
                order_quality_quantities = order.get('quality_quantities', {})
                for quality in qualities:
                    order_quality_quantities[quality] = st.number_input(
                        f"Ποσότητα για ποιότητα {quality}", 
                        min_value=0, max_value=100000, step=1, 
                        value=int(order_quality_quantities.get(quality, 0)),
                        key=f"order_quality_{quality}_{order_id if is_edit else 'new'}"
                    )
                
                executed_quantity = st.number_input(
                    "Εκτελεσθείσα Ποσότητα (kg)", 
                    min_value=0, max_value=100000, step=1, 
                    value=order.get('executed_quantity', 0)
                )
                
                agreed_price_per_kg = st.number_input(
                    "💰 Συμφωνηθείσα Τιμή ανά κιλό", 
                    min_value=0.0, max_value=100.0, step=0.01, 
                    value=order.get('agreed_price_per_kg', 0.0)
                )
                
                total_kg = sum(order_size_quantities.values()) + sum(order_quality_quantities.values())
                total_value = total_kg * agreed_price_per_kg if agreed_price_per_kg else 0
                
                if total_kg > 0:
                    st.info(f"📦 Σύνολο κιλών: {total_kg} kg")
                    st.success(f"💶 Συνολική αξία: {total_value:.2f} €")
                
                order_observations = st.text_area("📝 Παρατηρήσεις Παραγγελίας", value=order.get('observations', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("✅ Καταχώρηση Παραγγελίας")
            with col2:
                if is_edit:
                    if st.form_submit_button("❌ Ακύρωση Επεξεργασίας"):
                        st.session_state.edit_item = None
                        st.session_state.edit_type = None
                        clear_form_state(f"order_size_")
                        clear_form_state(f"order_quality_")
                        st.rerun()
            
            if submitted:
                with st.spinner("Καταχώρηση σε εξέλιξη..."):
                    if not customer_name:
                        st.error("❌ Παρακαλώ επιλέξτε πελάτη")
                    elif not variety:
                        st.error("❌ Παρακαλώ συμπληρώστε την ποικιλία")
                    elif total_kg <= 0:
                        st.error("❌ Η συνολική ποσότητα πρέπει να είναι μεγαλύτερη από 0")
                    else:
                        new_order = {
                            "id": order_id,
                            "date": order_date.strftime("%Y-%m-%d"),
                            "customer_id": customer_id,
                            "customer": customer_name,
                            "variety": variety,
                            "lot": lot_number,
                            "size_quantities": order_size_quantities,
                            "quality_quantities": order_quality_quantities,
                            "executed_quantity": executed_quantity,
                            "agreed_price_per_kg": agreed_price_per_kg,
                            "total_kg": total_kg,
                            "total_value": total_value,
                            "paid": paid_status,
                            "invoice_ref": invoice_ref,
                            "observations": order_observations,
                            "created_by": st.session_state.current_user,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        if is_edit:
                            for i, item in enumerate(st.session_state['orders']):
                                if item['id'] == order_id:
                                    st.session_state['orders'][i] = new_order
                                    break
                            st.success(f"✅ Η παραγγελία #{order_id} ενημερώθηκε επιτυχώς!")
                            logging.info(f"Order #{order_id} updated by {st.session_state.current_user}")
                        else:
                            st.session_state['orders'].append(new_order)
                            st.success(f"✅ Η παραγγελία #{order_id} καταχωρήθηκε επιτυχώς!")
                            logging.info(f"Order #{order_id} added by {st.session_state.current_user}")
                        
                        save_data({'orders': st.session_state['orders']})
                        st.session_state.edit_item = None
                        st.session_state.edit_type = None
                        clear_form_state(f"order_size_")
                        clear_form_state(f"order_quality_")

# Tab 4: Αναφορές
def show_reports():
    with tabs[3]:
        st.header("📈 Αναφορές και Εξαγωγές")
        
        report_type = st.selectbox("Επιλέξτε τύπο αναφοράς", [
            "Αναφορά Παραλαβών", 
            "Αναφορά Παραγγελιών", 
            "Αναφορά Πωλήσεων ανά Πελάτη",
            "Αναφορά Αποθηκευτικών Χώρων",
            "Αναφορά Παραγωγών ανά Παραγγελία"
        ])
        
        if report_type == "Αναφορά Παραλαβών":
            st.subheader("Αναφορά Παραλαβών")
            
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("Από ημερομηνία", value=datetime.today() - timedelta(days=30))
                end_date = st.date_input("Έως ημερομηνία", value=datetime.today())
                if start_date > end_date:
                    st.error("❌ Η αρχική ημερομηνία δεν μπορεί να είναι μετά την τελική")
                    return
                
                producer_options = ["Όλοι"] + [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
                selected_producer = st.selectbox("Παραγωγός", options=producer_options)
                
                cert_options = ["Όλες"] + ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
                selected_cert = st.selectbox("Πιστοποίηση", options=cert_options)
                
                sum_type = st.selectbox("Τύπος Αθροίσματος", ["Σύνολο", "Ανά Νούμερο", "Ανά Ποιότητα"])
            
            with col2:
                with st.spinner("Υπολογισμός αναφοράς..."):
                    filtered_receipts = []
                    for receipt in st.session_state['receipts']:
                        try:
                            receipt_date = datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date()
                        except (ValueError, KeyError):
                            continue
                        
                        if receipt_date < start_date or receipt_date > end_date:
                            continue
                        
                        if selected_producer != "Όλοι":
                            producer_id = int(selected_producer.split(" - ")[0])
                            if receipt.get('producer_id') != producer_id:
                                continue
                        
                        if selected_cert != "Όλες":
                            if selected_cert not in receipt.get('certifications', []):
                                continue
                        
                        filtered_receipts.append(receipt)
                
                if sum_type == "Σύνολο":
                    total_kg = sum(r['total_kg'] for r in filtered_receipts)
                    total_value = sum(r['total_value'] for r in filtered_receipts)
                elif sum_type == "Ανά Νούμερο":
                    size_totals = {}
                    for size in ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα", "Σκάρτα", "Μεταποίηση"]:
                        size_totals[size] = sum(r.get('size_quantities', {}).get(size, 0) for r in filtered_receipts)
                    total_kg = sum(size_totals.values())
                    total_value = sum(r['total_value'] for r in filtered_receipts)
                else:
                    quality_totals = {}
                    for quality in ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Διάφορα", "Μεταποίηση"]:
                        quality_totals[quality] = sum(r.get('quality_quantities', {}).get(quality, 0) for r in filtered_receipts)
                    total_kg = sum(quality_totals.values())
                    total_value = sum(r['total_value'] for r in filtered_receipts)
                
                st.metric("Συνολικές Παραλαβές", len(filtered_receipts))
                st.metric("Συνολικά Κιλά", f"{total_kg} kg")
                st.metric("Συνολική Αξία", f"{total_value:.2f} €")
                
                if sum_type == "Ανά Νούμερο" and size_totals:
                    st.write("**Ποσότητες ανά Νούμερο:**")
                    for size, quantity in size_totals.items():
                        if quantity > 0:
                            st.write(f"- {size}: {quantity} kg")
                
                if sum_type == "Ανά Ποιότητα" and quality_totals:
                    st.write("**Ποσότητες ανά Ποιότητα:**")
                    for quality, quantity in quality_totals.items():
                        if quantity > 0:
                            st.write(f"- {quality}: {quantity} kg")
            
            if filtered_receipts:
                df = pd.DataFrame(filtered_receipts)
                st.dataframe(df, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Εξαγωγή σε CSV",
                        data=csv_data,
                        file_name=f"αναφορά_παραλαβών_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                with col2:
                    excel_data = to_excel(df)
                    st.download_button(
                        label="📥 Εξαγωγή σε Excel",
                        data=excel_data,
                        file_name=f"αναφορά_παραλαβών_{start_date}_{end_date}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        
        elif report_type == "Αναφορά Παραγγελιών":
            st.subheader("Αναφορά Παραγγελιών")
            
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("Από ημερομηνία", value=datetime.today() - timedelta(days=30), key="orders_start")
                end_date = st.date_input("Έως ημερομηνία", value=datetime.today(), key="orders_end")
                if start_date > end_date:
                    st.error("❌ Η αρχική ημερομηνία δεν μπορεί να είναι μετά την τελική")
                    return
                
                sum_type = st.selectbox("Τύπος Αθροίσματος", ["Σύνολο", "Ανά Νούμερο", "Ανά Ποιότητα"], key="order_sum_type")
            
            with col2:
                with st.spinner("Υπολογισμός αναφοράς..."):
                    filtered_orders = []
                    for order in st.session_state['orders']:
                        try:
                            order_date = datetime.strptime(order['date'], '%Y-%m-%d').date()
                        except (ValueError, KeyError):
                            continue
                        
                        if order_date < start_date or order_date > end_date:
                            continue
                        
                        filtered_orders.append(order)
                
                if sum_type == "Σύνολο":
                    total_kg = sum(o.get('executed_quantity', 0) for o in filtered_orders)
                    total_value = sum(o['total_value'] for o in filtered_orders)
                elif sum_type == "Ανά Νούμερο":
                    size_totals = {}
                    for size in ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα", "Σκάρτα", "Μεταποίηση"]:
                        size_totals[size] = sum(o.get('size_quantities', {}).get(size, 0) for o in filtered_orders)
                    total_kg = sum(size_totals.values())
                    total_value = sum(o['total_value'] for o in filtered_orders)
                else:
                    quality_totals = {}
                    for quality in ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Διάφορα", "Μεταποίηση"]:
                        quality_totals[quality] = sum(o.get('quality_quantities', {}).get(quality, 0) for o in filtered_orders)
                    total_kg = sum(quality_totals.values())
                    total_value = sum(o['total_value'] for o in filtered_orders)
                
                executed_kg = sum(o.get('executed_quantity', 0) for o in filtered_orders)
                
                st.metric("Συνολικές Παραγγελίες", len(filtered_orders))
                st.metric("Συνολικά Κιλά", f"{total_kg} kg")
                st.metric("Εκτελεσθείσα Ποσότητα", f"{executed_kg} kg")
                st.metric("Συνολική Αξία", f"{total_value:.2f} €")
                
                if sum_type == "Ανά Νούμερο" and size_totals:
                    st.write("**Ποσότητες ανά Νούμερο:**")
                    for size, quantity in size_totals.items():
                        if quantity > 0:
                            st.write(f"- {size}: {quantity} kg")
                
                if sum_type == "Ανά Ποιότητα" and quality_totals:
                    st.write("**Ποσότητες ανά Ποιότητα:**")
                    for quality, quantity in quality_totals.items():
                        if quantity > 0:
                            st.write(f"- {quality}: {quantity} kg")
            
            if filtered_orders:
                df = pd.DataFrame(filtered_orders)
                st.dataframe(df, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Εξαγωγή σε CSV",
                        data=csv_data,
                        file_name=f"αναφορά_παραγγελιών_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                with col2:
                    excel_data = to_excel(df)
                    st.download_button(
                        label="📥 Εξαγωγή σε Excel",
                        data=excel_data,
                        file_name=f"αναφορά_παραγγελιών_{start_date}_{end_date}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        
        elif report_type == "Αναφορά Πωλήσεων ανά Πελάτη":
            st.subheader("Αναφορά Πωλήσεων ανά Πελάτη")
            
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("Από ημερομηνία", value=datetime.today() - timedelta(days=90), key="sales_start")
                end_date = st.date_input("Έως ημερομηνία", value=datetime.today(), key="sales_end")
                if start_date > end_date:
                    st.error("❌ Η αρχική ημερομηνία δεν μπορεί να είναι μετά την τελική")
                    return
                
                customer_options = ["Όλοι"] + [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
                selected_customer = st.selectbox("Πελάτης", options=customer_options)
            
            with col2:
                with st.spinner("Υπολογισμός αναφοράς..."):
                    customer_sales = {}
                    for order in st.session_state['orders']:
                        try:
                            order_date = datetime.strptime(order['date'], '%Y-%m-%d').date()
                        except (ValueError, KeyError):
                            continue
                        
                        if order_date < start_date or order_date > end_date:
                            continue
                        
                        if selected_customer != "Όλοι":
                            customer_id = int(selected_customer.split(" - ")[0])
                            if order.get('customer_id') != customer_id:
                                continue
                        
                        customer_name = order['customer']
                        if customer_name not in customer_sales:
                            customer_sales[customer_name] = {
                                'total_kg': 0,
                                'total_value': 0,
                                'orders_count': 0
                            }
                        
                        customer_sales[customer_name]['total_kg'] += order['total_kg']
                        customer_sales[customer_name]['total_value'] += order['total_value']
                        customer_sales[customer_name]['orders_count'] += 1
                
                for customer, data in customer_sales.items():
                    st.write(f"**{customer}**: {data['orders_count']} παραγγελίες, {data['total_kg']} kg, {data['total_value']:.2f}€")
                
                if customer_sales:
                    df = pd.DataFrame.from_dict(customer_sales, orient='index')
                    df.index.name = 'Πελάτης'
                    st.dataframe(df, use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        csv_data = df.to_csv().encode('utf-8')
                        st.download_button(
                            label="📥 Εξαγωγή σε CSV",
                            data=csv_data,
                            file_name=f"αναφορά_πωλήσεων_πελάτη_{start_date}_{end_date}.csv",
                            mime="text/csv"
                        )
                    with col2:
                        excel_data = to_excel(df)
                        st.download_button(
                            label="📥 Εξαγωγή σε Excel",
                            data=excel_data,
                            file_name=f"αναφορά_πωλήσεων_πελάτη_{start_date}_{end_date}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        
        elif report_type == "Αναφορά Παραγωγών ανά Παραγγελία":
            st.subheader("Αναφορά Παραγωγών ανά Παραγγελία")
            
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("Από ημερομηνία", value=datetime.today() - timedelta(days=90), key="producers_start")
                end_date = st.date_input("Έως ημερομηνία", value=datetime.today(), key="producers_end")
                if start_date > end_date:
                    st.error("❌ Η αρχική ημερομηνία δεν μπορεί να είναι μετά την τελική")
                    return
                
                producer_options = ["Όλοι"] + [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
                selected_producer = st.selectbox("Παραγωγός", options=producer_options)
            
            with col2:
                with st.spinner("Υπολογισμός αναφοράς..."):
                    producer_receipts = {}
                    for receipt in st.session_state['receipts']:
                        try:
                            receipt_date = datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date()
                        except (ValueError, KeyError):
                            continue
                        
                        if receipt_date < start_date or receipt_date > end_date:
                            continue
                        
                        if selected_producer != "Όλοι":
                            producer_id = int(selected_producer.split(" - ")[0])
                            if receipt.get('producer_id') != producer_id:
                                continue
                        
                        producer_name = receipt['producer_name']
                        if producer_name not in producer_receipts:
                            producer_receipts[producer_name] = {
                                'total_kg': 0,
                                'total_value': 0,
                                'receipts_count': 0,
                                'receipts': []
                            }
                        
                        producer_receipts[producer_name]['total_kg'] += receipt['total_kg']
                        producer_receipts[producer_name]['total_value'] += receipt['total_value']
                        producer_receipts[producer_name]['receipts_count'] = producer_receipts[producer_name].get('receipts_count', 0) + 1
                        producer_receipts[producer_name]['receipts'].append(receipt)
                
                for producer, data in producer_receipts.items():
                    st.write(f"**{producer}**: {data['receipts_count']} παραλαβές, {data['total_kg']} kg, {data['total_value']:.2f}€")
                    
                    with st.expander(f"Λεπτομέρειες για {producer}"):
                        for receipt in data['receipts']:
                            st.write(f"- Παραλαβή #{receipt['id']}: {receipt['total_kg']} kg, {receipt['total_value']:.2f}€ ({receipt['receipt_date']})")
                
                if producer_receipts:
                    export_data = []
                    for producer, data in producer_receipts.items():
                        for receipt in data['receipts']:
                            export_data.append({
                                'Παραγωγός': producer,
                                'Παραλαβή ID': receipt['id'],
                                'Ημερομηνία': receipt['receipt_date'],
                                'Ποσότητα (kg)': receipt['total_kg'],
                                'Αξία (€)': receipt['total_value'],
                                'LOT': receipt.get('lot', ''),
                                'Ποικιλία': receipt.get('variety', '')
                            })
                    
                    df = pd.DataFrame(export_data)
                    st.dataframe(df, use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Εξαγωγή σε CSV",
                            data=csv_data,
                            file_name=f"αναφορά_παραγωγών_{start_date}_{end_date}.csv",
                            mime="text/csv"
                        )
                    with col2:
                        excel_data = to_excel(df)
                        st.download_button(
                            label="📥 Εξαγωγή σε Excel",
                            data=excel_data,
                            file_name=f"αναφορά_παραγωγών_{start_date}_{end_date}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        
        else:
            st.subheader("Αναφορά Αποθηκευτικών Χώρων")
            
            storage_usage = calculate_storage_usage()
            
            for loc_id, data in storage_usage.items():
                with st.expander(f"{data['name']} - {data['used']}/{data['capacity']} kg ({data['used']/data['capacity']*100:.1f}%)"):
                    st.progress(data['used'] / data['capacity'])
                    
                    if data['items']:
                        st.write("**Περιεχόμενα:**")
                        for item in data['items']:
                            st.write(f"- Παραλαβή #{item['id']}: {item['kg']} kg ({item['date']})")
                    else:
                        st.info("Δεν υπάρχουν παραλαβές σε αυτόν τον χώρο")
            
            df = pd.DataFrame.from_dict(storage_usage, orient='index')
            st.dataframe(df, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                csv_data = df.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Εξαγωγή σε CSV",
                    data=csv_data,
                    file_name="αναφορά_αποθηκευτικών_χώρων.csv",
                    mime="text/csv"
                )
            with col2:
                excel_data = to_excel(df)
                st.download_button(
                    label="📥 Εξαγωγή σε Excel",
                    data=excel_data,
                    file_name="αναφορά_αποθηκευτικών_χώρων.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# Tab 5: Διαχείριση
def show_management():
    with tabs[4]:
        if not can_edit():
            st.warning("⛔ Δεν έχετε δικαιώματα για διαχείριση οντοτήτων")
            return
        
        st.header("⚙️ Διαχείριση Οντοτήτων")
        
        entity_type = st.selectbox("Επιλέξτε τύπο οντότητας", ["Παραγωγοί", "Πελάτες"])
        
        if entity_type == "Παραγωγοί":
            entities = st.session_state['producers']
            entity_key = 'producers'
        else:
            entities = st.session_state['customers']
            entity_key = 'customers'
        
        st.subheader(f"Διαχείριση {entity_type}")
        
        with st.form(f"{entity_key}_form", clear_on_submit=True):
            entity_id = st.number_input("ID", min_value=1, step=1, value=get_next_id(entities))
            name = st.text_input("Όνομα")
            
            if entity_type == "Παραγωγοί":
                quantity = st.number_input("Ποσότητα", min_value=0, max_value=100000, step=1)
                certifications_options = ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
                certifications = st.multiselect("Πιστοποιήσεις", certifications_options)
            else:
                address = st.text_input("Διεύθυνση")
                phone = st.text_input("Τηλέφωνο")
            
            submitted = st.form_submit_button("💾 Προσθήκη")
            
            if submitted:
                with st.spinner("Προσθήκη σε εξέλιξη..."):
                    if not name:
                        st.error("❌ Παρακαλώ συμπληρώστε το όνομα")
                    else:
                        if entity_type == "Παραγωγοί":
                            new_entity = {
                                "id": entity_id,
                                "name": name,
                                "quantity": quantity,
                                "certifications": certifications
                            }
                        else:
                            new_entity = {
                                "id": entity_id,
                                "name": name,
                                "address": address,
                                "phone": phone
                            }
                        
                        entities.append(new_entity)
                        st.session_state[entity_key] = entities
                        save_data({entity_key: entities})
                        st.success(f"✅ Προστέθηκε νέος {entity_type[:-1]} #{entity_id}")
                        logging.info(f"Added {entity_type[:-1]} #{entity_id} by {st.session_state.current_user}")
                        clear_form_state(f"{entity_key}_")
        
        st.subheader(f"Κατάλογος {entity_type}")
        if entities:
            for item in entities:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{item['name']}** (ID: {item['id']})")
                    if entity_type == "Παραγωγοί":
                        st.write(f"Ποσότητα: {item.get('quantity', 0)} kg")
                        st.write(f"Πιστοποιήσεις: {', '.join(item.get('certifications', []))}")
                    else:
                        st.write(f"Τηλ: {item.get('phone', '')}")
                with col2:
                    if can_delete() and st.button("🗑️ Διαγραφή", key=f"del_{item['id']}"):
                        st.session_state[entity_key] = [i for i in entities if i['id'] != item['id']]
                        save_data({entity_key: st.session_state[entity_key]})
                        st.success(f"✅ Διαγραφή {entity_type[:-1]} #{item['id']} επιτυχής!")
                        logging.info(f"Deleted {entity_type[:-1]} #{item['id']} by {st.session_state.current_user}")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info(f"Δεν υπάρχουν καταχωρημένοι {entity_type}")

# Tab 6: Διαχείριση Χρηστών
def show_user_management():
    with tabs[5]:
        if st.session_state.user_role != 'admin':
            st.warning("⛔ Δεν έχετε δικαιώματα διαχείρισης χρηστών")
            return
        
        st.header("👥 Διαχείριση Χρηστών")
        
        st.subheader("Υπάρχοντες Χρήστες")
        users_df = pd.DataFrame([
            {'username': user, 'role': data['role'], 'full_name': data.get('full_name', '')}
            for user, data in st.session_state['users'].items()
        ])
        st.dataframe(users_df, use_container_width=True)
        
        st.subheader("Δημιουργία Νέου Χρήστη")
        with st.form("new_user_form", clear_on_submit=True):
            new_username = st.text_input("Νέο Όνομα Χρήστη")
            new_password = st.text_input("Νέος Κωδικός", type="password")
            confirm_password = st.text_input("Επιβεβαίωση Κωδικού", type="password")
            new_role = st.selectbox("Ρόλος", ["viewer", "editor", "admin"])
            new_fullname = st.text_input("Πλήρες Όνομα")
            
            if st.form_submit_button("➕ Δημιουργία Χρήστη"):
                with st.spinner("Δημιουργία χρήστη σε εξέλιξη..."):
                    if not new_username or not new_password:
                        st.error("❌ Παρακαλώ συμπληρώστε όλα τα πεδία")
                    elif new_password != confirm_password:
                        st.error("❌ Οι κωδικοί δεν ταιριάζουν")
                    elif new_username in st.session_state['users']:
                        st.error("❌ Το όνομα χρήστη υπάρχει ήδη")
                    else:
                        st.session_state['users'][new_username] = {
                            'password': hash_password(new_password),
                            'role': new_role,
                            'full_name': new_fullname
                        }
                        save_data({'users': st.session_state['users']})
                        st.success(f"✅ Ο χρήστης {new_username} δημιουργήθηκε!")
                        logging.info(f"User {new_username} created by {st.session_state.current_user}")
                        clear_form_state("new_user_")
        
        st.subheader("Διαχείριση Υφιστάμενων Χρηστών")
        user_options = list(st.session_state['users'].keys())
        selected_user = st.selectbox("Επιλέξτε χρήστη για διαχείριση", user_options)
        
        if selected_user:
            user_data = st.session_state['users'][selected_user]
            
            col1, col2 = st.columns(2)
            
            with col1:
                with st.form("change_password_form", clear_on_submit=True):
                    st.write(f"**Αλλαγή Κωδικού για: {selected_user}**")
                    new_password = st.text_input("Νέος Κωδικός", type="password", key="new_pass")
                    confirm_password = st.text_input("Επιβεβαίωση Κωδικού", type="password", key="confirm_pass")
                    
                    if st.form_submit_button("🔒 Αλλαγή Κωδικού"):
                        with st.spinner("Αλλαγή κωδικού σε εξέλιξη..."):
                            if new_password != confirm_password:
                                st.error("❌ Οι κωδικοί δεν ταιριάζουν")
                            elif not new_password:
                                st.error("❌ Παρακαλώ εισάγετε νέο κωδικό")
                            else:
                                st.session_state['users'][selected_user]['password'] = hash_password(new_password)
                                save_data({'users': st.session_state['users']})
                                st.success(f"✅ Ο κωδικός για τον χρήστη {selected_user} άλλαξε επιτυχώς!")
                                logging.info(f"Password changed for {selected_user} by {st.session_state.current_user}")
                                clear_form_state("new_pass")
                                clear_form_state("confirm_pass")
            
            with col2:
                with st.form("change_role_form", clear_on_submit=True):
                    st.write(f"**Αλλαγή Ρόλου για: {selected_user}**")
                    new_role = st.selectbox("Νέος Ρόλος", ["viewer", "editor", "admin"], 
                                          index=["viewer", "editor", "admin"].index(user_data['role']))
                    
                    if st.form_submit_button("🎭 Αλλαγή Ρόλου"):
                        with st.spinner("Αλλαγή ρόλου σε εξέλιξη..."):
                            st.session_state['users'][selected_user]['role'] = new_role
                            save_data({'users': st.session_state['users']})
                            st.success(f"✅ Ο ρόλος για τον χρήστη {selected_user} άλλαξε επιτυχώς!")
                            logging.info(f"Role changed for {selected_user} to {new_role} by {st.session_state.current_user}")
                    
                    if selected_user != 'admin' and st.button("🗑️ Διαγραφή Χρήστη", key=f"del_user_{selected_user}"):
                        del st.session_state['users'][selected_user]
                        save_data({'users': st.session_state['users']})
                        st.success(f"✅ Ο χρήστης {selected_user} διαγράφηκε!")
                        logging.info(f"User {selected_user} deleted by {st.session_state.current_user}")
                        time.sleep(1)
                        st.rerun()

# Tab 7: Αποθηκευτικοί Χώροι
def show_storage_management():
    with tabs[6]:
        if st.session_state.user_role != 'admin':
            st.warning("⛔ Δεν έχετε δικαιώματα διαχείρισης αποθηκευτικών χώρων")
            return
        
        st.header("🏢 Διαχείριση Αποθηκευτικών Χώρων")
        
        st.subheader("Προσθήκη Νέου Αποθηκευτικού Χώρου")
        with st.form("new_storage_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                storage_id = st.number_input("ID Αποθήκης", min_value=1, step=1, value=get_next_id(st.session_state['storage_locations']))
                storage_name = st.text_input("Όνομα Αποθήκης")
            
            with col2:
                storage_capacity = st.number_input("Χωρητικότητα (kg)", min_value=1, max_value=1000000, step=1, value=1000)
                storage_description = st.text_input("Περιγραφή")
            
            if st.form_submit_button("➕ Προσθήκη Αποθήκης"):
                with st.spinner("Προσθήκη αποθήκης σε εξέλιξη..."):
                    if not storage_name:
                        st.error("❌ Παρακαλώ συμπληρώστε το όνομα αποθήκης")
                    else:
                        new_storage = {
                            "id": storage_id,
                            "name": storage_name,
                            "capacity": storage_capacity,
                            "description": storage_description
                        }
                        
                        st.session_state['storage_locations'].append(new_storage)
                        save_data({'storage_locations': st.session_state['storage_locations']})
                        st.success(f"✅ Η αποθήκη {storage_name} προστέθηκε!")
                        logging.info(f"Storage location {storage_name} added by {st.session_state.current_user}")
                        clear_form_state("new_storage_")
        
        st.subheader("Κατάλογος Αποθηκευτικών Χώρων")
        if st.session_state['storage_locations']:
            for location in st.session_state['storage_locations']:
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{location['name']}** (ID: {location['id']})")
                    st.write(f"Χωρητικότητα: {location['capacity']} kg")
                    st.write(f"Περιγραφή: {location.get('description', '')}")
                
                with col2:
                    used_space = 0
                    for receipt in st.session_state['receipts']:
                        if receipt.get('storage_location_id') == location['id']:
                            used_space += receipt['total_kg']
                    
                    st.write(f"Χρησιμοποιημένος χώρος: {used_space} kg")
                    st.write(f"Διαθέσιμος χώρος: {location['capacity'] - used_space} kg")
                    st.progress(used_space / location['capacity'])
                
                with col3:
                    if can_delete() and st.button("🗑️ Διαγραφή", key=f"del_storage_{location['id']}"):
                        if any(receipt.get('storage_location_id') == location['id'] for receipt in st.session_state['receipts']):
                            st.error("❌ Δεν μπορείτε να διαγράψετε αποθήκη που περιέχει παραλαβές")
                        else:
                            st.session_state['storage_locations'] = [
                                loc for loc in st.session_state['storage_locations'] if loc['id'] != location['id']
                            ]
                            save_data({'storage_locations': st.session_state['storage_locations']})
                            st.success(f"✅ Η αποθήκη {location['name']} διαγράφηκε!")
                            logging.info(f"Storage location {location['name']} deleted by {st.session_state.current_user}")
                            time.sleep(1)
                            st.rerun()
        else:
            st.info("Δεν υπάρχουν καταχωρημένοι αποθηκευτικοί χώροι")

# Εμφάνιση της σωστής καρτέλας βάσει επιλογής
def show_tab(tab_index):
    if tab_index == 0:
        show_central_database()
    elif tab_index == 1:
        show_new_receipt()
    elif tab_index == 2:
        show_new_order()
    elif tab_index == 3:
        show_reports()
    elif tab_index == 4:
        show_management()
    elif tab_index == 5 and st.session_state.user_role == 'admin':
        show_user_management()
    elif tab_index == 6 and st.session_state.user_role == 'admin':
        show_storage_management()

current_tab_index = menu_options.index(st.session_state.current_tab)
show_tab(current_tab_index)

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**Οδηγίες Χρήσης:**
- Χρησιμοποιήστε τις καρτέλες για να πλοηγηθείτε στο σύστημα
- Προσθέστε νέες παραλαβές και παραγγελίες
- Δημιουργήστε αναφορές και εξάγετε δεδομένα
- Οι διαχειριστές μπορούν να διαχειρίζονται χρήστες και αποθήκες
""")

# Κουμπί εκτύπωσης αναφορών
if st.sidebar.button("🖨️ Εκτύπωση Αναφορών"):
    st.sidebar.success("📋 Οι αναφορές είναι έτοιμες για εκτύπωση!")
    logging.info(f"Print reports requested by {st.session_state.current_user}")

# Κουμπί ανανέωσης δεδομένων
if st.sidebar.button("🔄 Ανανέωση Δεδομένων"):
    data = load_data()
    for key, value in data.items():
        st.session_state[key] = value
    st.sidebar.success("✅ Τα δεδομένα ανανεώθηκαν!")
    logging.info(f"Data refreshed by {st.session_state.current_user}")

# Παράδειγμα κώδικα για SQLite (σχολιασμένο)
"""
# Παράδειγμα χρήσης SQLite αντί για JSON
import sqlite3

def init_db():
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY,
        receipt_date TEXT,
        producer_id INTEGER,
        producer_name TEXT,
        variety TEXT,
        lot TEXT,
        storage_location_id INTEGER,
        storage_location TEXT,
        size_quantities TEXT,
        quality_quantities TEXT,
        certifications TEXT,
        agreed_price_per_kg REAL,
        total_kg REAL,
        total_value REAL,
        paid TEXT,
        invoice_ref TEXT,
        observations TEXT,
        created_by TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

def load_data_db():
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute("SELECT * FROM receipts")
    receipts = c.fetchall()
    conn.close()
    return receipts
"""