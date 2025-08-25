import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import csv
from io import BytesIO
import os
import hashlib
import time

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
    return hashlib.sha256(password.encode()).hexdigest()

def init_data():
    """Αρχικοποίηση όλων των δεδομένων"""
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
    
    if not os.path.exists('storage_locations.json'):
        storage_locations = [
            {"id": 1, "name": "Αποθήκη Α", "capacity": 10000, "description": "Κύρια αποθήκη"},
            {"id": 2, "name": "Αποθήκη Β", "capacity": 5000, "description": "Δευτερεύουσα αποθήκη"}
        ]
        with open('storage_locations.json', 'w', encoding='utf-8') as f:
            json.dump(storage_locations, f, ensure_ascii=False, indent=2)

# Συναρτήσεις αυτόματης αποθήκευσης και φόρτωσης
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
                data[key] = []
        except:
            data[key] = []
    
    return data

def save_data(data):
    """Αποθήκευση δεδομένων σε αρχεία"""
    for key, value in data.items():
        with open(f'{key}.json', 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)

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
                if st.session_state['users'][username]['password'] == hash_password(password):
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.session_state.user_role = st.session_state['users'][username]['role']
                    st.success("Επιτυχής σύνδεση!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Λάθος κωδικός πρόσβασης")
            else:
                st.error("Ο χρήστης δεν υπάρχει")

# Συνάρτηση αποσύνδεσης
def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.edit_item = None
    st.session_state.edit_type = None
    st.success("Αποσυνδεθήκατε επιτυχώς")
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

if not st.session_state['customers']:
    st.session_state['customers'] = [
        {"id": 1, "name": "Πελάτης Α", "address": "Διεύθυνση 1", "phone": "2101111111"},
        {"id": 2, "name": "Πελάτης Β", "address": "Διεύθυνση 2", "phone": "2102222222"}
    ]
    save_data({'customers': st.session_state['customers']})

# Πλαϊνό μενού για γρήγορη πρόσβαση
st.sidebar.header("📋 Γρήγορη Πρόσβαση")
menu_options = [
    "Κεντρική Βάση", 
    "Νέα Παραλαβή", 
    "Νέα Παραγγελία", 
    "Αναφορές", 
    "Διαχείριση", 
    "Διαχείριση Χρηστών", 
    "Αποθηκευτικοί Χώροι"
]

# Χρήση selectbox αντί για radio για καλύτερη λειτουργία
selected_menu = st.sidebar.selectbox("Επιλέξτε ενότητα", menu_options, 
                                    index=menu_options.index(st.session_state.current_tab))

# Ενημέρωση του τρέχοντος tab
st.session_state.current_tab = selected_menu

# Στήλες για το tab layout
tabs = st.tabs(menu_options)

# Βοηθητική συνάρτηση για εμφάνιση της σωστής καρτέλας
def show_tab(tab_index):
    """Εμφάνιση της σωστής καρτέλας βάσει επιλογής"""
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
    elif tab_index == 5:
        show_user_management()
    elif tab_index == 6:
        show_storage_management()

# Tab 1: Κεντρική Βάση
def show_central_database():
    with tabs[0]:
        st.header("📊 Κεντρική Βάση Δεδομένων")
        
        # Επιλογή τύπου δεδομένων για επεξεργασία
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
            # Πίνακας δεδομένων
            df = pd.DataFrame(items)
            if not df.empty:
                # Εμφάνιση μόνο των επιλεγμένων στηλών
                display_columns = [col for col in columns if col in df.columns]
                st.dataframe(df[display_columns], use_container_width=True)
                
                # Επιλογή εγγραφής για επεξεργασία/διαγραφή
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
                            
                            if st.button("✏️ Επεξεργασία"):
                                st.session_state.edit_item = selected_item
                                st.session_state.edit_type = item_key
                                if item_key == 'receipts':
                                    st.session_state.current_tab = "Νέα Παραλαβή"
                                else:
                                    st.session_state.current_tab = "Νέα Παραγγελία"
                                st.rerun()
                            
                            if can_delete() and st.button("🗑️ Διαγραφή"):
                                st.session_state[item_key] = [item for item in items if item['id'] != selected_id]
                                save_data({item_key: st.session_state[item_key]})
                                st.success("✅ Διαγραφή επιτυχής!")
                                time.sleep(1)
                                st.rerun()
            else:
                st.info(f"Δεν υπάρχουν καταχωρημένες {data_type}")
        else:
            st.info(f"Δεν υπάρχουν καταχωρημένες {data_type}")

# Tab 2: Νέα Παραλαβή
def show_new_receipt():
    with tabs[1]:
        # Έλεγχος αν υπάρχει προς επεξεργασία στοιχείο
        if st.session_state.edit_item and st.session_state.edit_type == 'receipts':
            receipt = st.session_state.edit_item
            is_edit = True
            st.header("📝 Επεξεργασία Παραλαβής")
        else:
            receipt = {}
            is_edit = False
            st.header("📥 Καταχώρηση Νέας Παραλαβής")
        
        with st.form("receipt_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                if is_edit:
                    receipt_id = st.number_input("Αριθμός Παραλαβής", value=receipt['id'], disabled=True)
                    st.text_input("Αριθμός LOT", value=receipt.get('lot', ''), disabled=True)
                else:
                    receipt_id = st.number_input("Αριθμός Παραλαβής", min_value=1, step=1, value=get_next_id(st.session_state['receipts']))
                
                # Επιλογή ημερομηνίας
                if is_edit:
                    receipt_date = st.date_input("Ημερομηνία Παραλαβής", value=datetime.strptime(receipt['receipt_date'], '%Y-%m-%d'))
                else:
                    receipt_date = st.date_input("Ημερομηνία Παραλαβής", value=datetime.today())
                
                # Επιλογή παραγωγού
                producer_options = [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
                default_index = 0
                if is_edit and 'producer_id' in receipt:
                    default_index = next((i for i, p in enumerate(producer_options) if str(receipt['producer_id']) in p), 0)
                selected_producer = st.selectbox("Παραγωγός", options=producer_options, index=default_index)
                producer_id = int(selected_producer.split(" - ")[0]) if selected_producer else None
                producer_name = selected_producer.split(" - ")[1] if selected_producer else ""
                
                variety = st.text_input("Ποικιλία", value=receipt.get('variety', ''))
                
                # Αυτόματη δημιουργία LOT
                if variety and producer_id and receipt_date:
                    lot_number = generate_lot_number(receipt_date, producer_id, variety)
                    if not is_edit:
                        st.text_input("Αριθμός LOT", value=lot_number, disabled=True)
                else:
                    lot_number = receipt.get('lot', '')
                
                # Επιλογή αποθηκευτικού χώρου
                storage_options = [f"{s['id']} - {s['name']}" for s in st.session_state['storage_locations']]
                default_storage_index = 0
                if is_edit and 'storage_location_id' in receipt:
                    default_storage_index = next((i for i, s in enumerate(storage_options) if str(receipt['storage_location_id']) in s), 0)
                selected_storage = st.selectbox("Αποθηκευτικός Χώρος", options=storage_options, index=default_storage_index)
                storage_id = int(selected_storage.split(" - ")[0]) if selected_storage else None
                
                # Πληρωμή
                paid_options = ["Ναι", "Όχι"]
                paid_index = 0 if receipt.get('paid') == "Ναι" else 1
                paid_status = st.selectbox("Πληρώθηκε;", paid_options, index=paid_index)
                
                # Σχετικό τιμολόγιο
                invoice_ref = st.text_input("Σχετικό Τιμολόγιο", value=receipt.get('invoice_ref', ''))
            
            with col2:
                # Ποσότητες ανά νούμερο
                st.subheader("📊 Ποσότητες ανά Νούμερο")
                sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα", "Σκάρτα", "Μεταποίηση"]
                size_quantities = receipt.get('size_quantities', {})
                for size in sizes:
                    size_quantities[size] = st.number_input(
                        f"Ποσότητα για νούμερο {size}", 
                        min_value=0, step=1, 
                        value=int(size_quantities.get(size, 0)),
                        key=f"size_{size}_{receipt_id if is_edit else 'new'}"
                    )
                
                # Ποσότητες ανά ποιότητα
                st.subheader("📊 Ποσότητες ανά Ποιότητα")
                qualities = ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Διάφορα", "Μεταποίηση"]
                quality_quantities = receipt.get('quality_quantities', {})
                for quality in qualities:
                    quality_quantities[quality] = st.number_input(
                        f"Ποσότητα για ποιότητα {quality}", 
                        min_value=0, step=1, 
                        value=int(quality_quantities.get(quality, 0)),
                        key=f"quality_{quality}_{receipt_id if is_edit else 'new'}"
                    )
                
                # Πιστοποιήσεις
                certifications = st.multiselect(
                    "📑 Πιστοποιήσεις",
                    ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"],
                    default=receipt.get('certifications', [])
                )
                
                # Συμφωνηθείσα τιμή
                agreed_price_per_kg = st.number_input(
                    "💰 Συμφωνηθείσα Τιμή ανά κιλό", 
                    min_value=0.0, step=0.01, 
                    value=receipt.get('agreed_price_per_kg', 0.0)
                )
                
                # Υπολογισμός συνολικής αξίας
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
                        st.rerun()
            
            if submitted:
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
                    # Ενημέρωση υπάρχουσας παραλαβής
                    for i, item in enumerate(st.session_state['receipts']):
                        if item['id'] == receipt_id:
                            st.session_state['receipts'][i] = new_receipt
                            break
                    st.success(f"✅ Η παραλαβή #{receipt_id} ενημερώθηκε επιτυχώς!")
                else:
                    # Προσθήκη νέας παραλαβής
                    st.session_state['receipts'].append(new_receipt)
                    st.success(f"✅ Η παραλαβή #{receipt_id} καταχωρήθηκε επιτυχώς!")
                
                save_data({'receipts': st.session_state['receipts']})
                st.session_state.edit_item = None
                st.session_state.edit_type = None
                time.sleep(2)
                st.rerun()

# Tab 3: Νέα Παραγγελία
def show_new_order():
    with tabs[2]:
        # Έλεγχος αν υπάρχει προς επεξεργασία στοιχείο
        if st.session_state.edit_item and st.session_state.edit_type == 'orders':
            order = st.session_state.edit_item
            is_edit = True
            st.header("📝 Επεξεργασία Παραγγελίας")
        else:
            order = {}
            is_edit = False
            st.header("📋 Καταχώρηση Νέας Παραγγελίας")
        
        with st.form("order_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                if is_edit:
                    order_id = st.number_input("Αριθμός Παραγγελίας", value=order['id'], disabled=True)
                    st.text_input("Αριθμός LOT", value=order.get('lot', ''), disabled=True)
                else:
                    order_id = st.number_input("Αριθμός Παραγγελίας", min_value=1, step=1, value=get_next_id(st.session_state['orders']))
                
                if is_edit:
                    order_date = st.date_input("Ημερομηνία Παραγγελίας", value=datetime.strptime(order['date'], '%Y-%m-%d'))
                else:
                    order_date = st.date_input("Ημερομηνία Παραγγελίας", value=datetime.today())
                
                # Επιλογή πελάτη
                customer_options = [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
                default_customer_index = 0
                if is_edit and 'customer_id' in order:
                    default_customer_index = next((i for i, c in enumerate(customer_options) if str(order['customer_id']) in c), 0)
                selected_customer = st.selectbox("Πελάτης", options=customer_options, index=default_customer_index)
                customer_id = int(selected_customer.split(" - ")[0]) if selected_customer else None
                customer_name = selected_customer.split(" - ")[1] if selected_customer else ""
                
                variety = st.text_input("Ποικιλία Παραγγελίας", value=order.get('variety', ''))
                
                # Αυτόματη δημιουργία LOT
                if variety and customer_id and order_date:
                    lot_number = generate_lot_number(order_date, customer_id, variety)
                    if not is_edit:
                        st.text_input("Αριθμός LOT", value=lot_number, disabled=True)
                else:
                    lot_number = order.get('lot', '')
                
                # Πληρωμή
                paid_options = ["Ναι", "Όχι"]
                paid_index = 0 if order.get('paid') == "Ναι" else 1
                paid_status = st.selectbox("Πληρώθηκε;", paid_options, index=paid_index)
                
                # Σχετικό τιμολόγιο
                invoice_ref = st.text_input("Σχετικό Τιμολόγιο", value=order.get('invoice_ref', ''))
            
            with col2:
                # Ποσότητες παραγγελίας ανά νούμερο
                st.subheader("📦 Ποσότητες Παραγγελίας ανά Νούμερο")
                sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα", "Σκάρτα", "Μεταποίηση"]
                order_size_quantities = order.get('size_quantities', {})
                for size in sizes:
                    order_size_quantities[size] = st.number_input(
                        f"Ποσότητα για νούμερο {size}", 
                        min_value=0, step=1, 
                        value=int(order_size_quantities.get(size, 0)),
                        key=f"order_size_{size}_{order_id if is_edit else 'new'}"
                    )
                
                # Ποσότητες παραγγελίας ανά ποιότητα
                st.subheader("📦 Ποσότητες Παραγγελίας ανά Ποιότητα")
                qualities = ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Διάφορα", "Μεταποίηση"]
                order_quality_quantities = order.get('quality_quantities', {})
                for quality in qualities:
                    order_quality_quantities[quality] = st.number_input(
                        f"Ποσότητα για ποιότητα {quality}", 
                        min_value=0, step=1, 
                        value=int(order_quality_quantities.get(quality, 0)),
                        key=f"order_quality_{quality}_{order_id if is_edit else 'new'}"
                    )
                
                # Εκτελεσθείσα ποσότητα
                executed_quantity = st.number_input(
                    "Εκτελεσθείσα Ποσότητα (kg)", 
                    min_value=0, step=1, 
                    value=order.get('executed_quantity', 0)
                )
                
                # Συμφωνηθείσα τιμή
                agreed_price_per_kg = st.number_input(
                    "💰 Συμφωνηθείσα Τιμή ανά κιλό", 
                    min_value=0.0, step=0.01, 
                    value=order.get('agreed_price_per_kg', 0.0)
                )
                
                # Υπολογισμός συνολικής αξίας
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
                        st.rerun()
            
            if submitted:
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
                    # Ενημέρωση υπάρχουσας παραγγελίας
                    for i, item in enumerate(st.session_state['orders']):
                        if item['id'] == order_id:
                            st.session_state['orders'][i] = new_order
                            break
                    st.success(f"✅ Η παραγγελία #{order_id} ενημερώθηκε επιτυχώς!")
                else:
                    # Προσθήκη νέας παραγγελίας
                    st.session_state['orders'].append(new_order)
                    st.success(f"✅ Η παραγγελία #{order_id} καταχωρήθηκε επιτυχώς!")
                
                save_data({'orders': st.session_state['orders']})
                st.session_state.edit_item = None
                st.session_state.edit_type = None
                time.sleep(2)
                st.rerun()

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
                
                producer_options = ["Όλοι"] + [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
                selected_producer = st.selectbox("Παραγωγός", options=producer_options)
                
                cert_options = ["Όλες"] + ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
                selected_cert = st.selectbox("Πιστοποίηση", options=cert_options)
                
                # Επιλογή τύπου αθροίσματος
                sum_type = st.selectbox("Τύπος Αθροίσματος", ["Σύνολο", "Ανά Νούμερο", "Ανά Ποιότητα"])
            
            with col2:
                filtered_receipts = []
                for receipt in st.session_state['receipts']:
                    receipt_date = datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date()
                    
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
                
                # Υπολογισμός συνολικών ποσοτήτων
                if sum_type == "Σύνολο":
                    total_kg = sum(r['total_kg'] for r in filtered_receipts)
                    total_value = sum(r['total_value'] for r in filtered_receipts)
                elif sum_type == "Ανά Νούμερο":
                    # Υπολογισμός ποσοτήτων ανά νούμερο
                    size_totals = {}
                    for size in ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα", "Σκάρτα", "Μεταποίηση"]:
                        size_totals[size] = sum(r.get('size_quantities', {}).get(size, 0) for r in filtered_receipts)
                    total_kg = sum(size_totals.values())
                    total_value = sum(r['total_value'] for r in filtered_receipts)
                else:  # Ανά Ποιότητα
                    # Υπολογισμός ποσοτήτων ανά ποιότητα
                    quality_totals = {}
                    for quality in ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Διάφορα", "Μεταποίηση"]:
                        quality_totals[quality] = sum(r.get('quality_quantities', {}).get(quality, 0) for r in filtered_receipts)
                    total_kg = sum(quality_totals.values())
                    total_value = sum(r['total_value'] for r in filtered_receipts)
                
                st.metric("Συνολικές Παραλαβές", len(filtered_receipts))
                st.metric("Συνολικά Κιλά", f"{total_kg} kg")
                st.metric("Συνολική Αξία", f"{total_value:.2f} €")
                
                # Εμφάνιση αναλυτικών ποσοτήτων
                if sum_type == "Ανά Νούμερο" and size_totals:
                    st.write("**Ποσότητες ανά Νούμερο:**")
                    for size, quantity in size_totals.items():
                        if quantity > 0:
                            st.write(f"- Νούμερο {size}: {quantity} kg")
                
                if sum_type == "Ανά Ποιότητα" and quality_totals:
                    st.write("**Ποσότητες ανά Ποιότητα:**")
                    for quality, quantity in quality_totals.items():
                        if quantity > 0:
                            st.write(f"- Ποιότητα {quality}: {quantity} kg")
            
            # Πίνακας παραλαβών
            if filtered_receipts:
                df = pd.DataFrame(filtered_receipts)
                st.dataframe(df[['id', 'receipt_date', 'producer_name', 'total_kg', 'total_value', 'lot']], use_container_width=True)
                
                # Εξαγωγή σε CSV
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Εξαγωγή σε CSV",
                    data=csv_data,
                    file_name=f"receipts_report_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Δεν βρέθηκαν παραλαβές για τα επιλεγμένα κριτήρια")
        
        elif report_type == "Αναφορά Παραγγελιών":
            st.subheader("Αναφορά Παραγγελιών")
            
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("Από ημερομηνία", value=datetime.today() - timedelta(days=30))
                end_date = st.date_input("Έως ημερομηνία", value=datetime.today())
                
                customer_options = ["Όλοι"] + [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
                selected_customer = st.selectbox("Πελάτης", options=customer_options)
                
                # Επιλογή τύπου αθροίσματος
                sum_type = st.selectbox("Τύπος Αθροίσματος", ["Σύνολο", "Ανά Νούμερο", "Ανά Ποιότητα"])
            
            with col2:
                filtered_orders = []
                for order in st.session_state['orders']:
                    order_date = datetime.strptime(order['date'], '%Y-%m-%d').date()
                    
                    if order_date < start_date or order_date > end_date:
                        continue
                    
                    if selected_customer != "Όλοι":
                        customer_id = int(selected_customer.split(" - ")[0])
                        if order.get('customer_id') != customer_id:
                            continue
                    
                    filtered_orders.append(order)
                
                # Υπολογισμός συνολικών ποσοτήτων
                if sum_type == "Σύνολο":
                    total_kg = sum(o['total_kg'] for o in filtered_orders)
                    total_value = sum(o['total_value'] for o in filtered_orders)
                    executed_kg = sum(o['executed_quantity'] for o in filtered_orders)
                elif sum_type == "Ανά Νούμερο":
                    # Υπολογισμός ποσοτήτων ανά νούμερο
                    size_totals = {}
                    for size in ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα", "Σκάρτα", "Μεταποίηση"]:
                        size_totals[size] = sum(o.get('size_quantities', {}).get(size, 0) for o in filtered_orders)
                    total_kg = sum(size_totals.values())
                    total_value = sum(o['total_value'] for o in filtered_orders)
                    executed_kg = sum(o['executed_quantity'] for o in filtered_orders)
                else:  # Ανά Ποιότητα
                    # Υπολογισμός ποσοτήτων ανά ποιότητα
                    quality_totals = {}
                    for quality in ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Διάφορα", "Μεταποίηση"]:
                        quality_totals[quality] = sum(o.get('quality_quantities', {}).get(quality, 0) for o in filtered_orders)
                    total_kg = sum(quality_totals.values())
                    total_value = sum(o['total_value'] for o in filtered_orders)
                    executed_kg = sum(o['executed_quantity'] for o in filtered_orders)
                
                st.metric("Συνολικές Παραγγελίες", len(filtered_orders))
                st.metric("Συνολικά Κιλά", f"{total_kg} kg")
                st.metric("Συνολική Αξία", f"{total_value:.2f} €")
                st.metric("Εκτελεσμένα Κιλά", f"{executed_kg} kg")
                
                # Υπολογισμός ποσοστού εκτέλεσης
                if total_kg > 0:
                    execution_percentage = (executed_kg / total_kg) * 100
                    st.metric("Ποσοστό Εκτέλεσης", f"{execution_percentage:.1f}%")
                
                # Εμφάνιση αναλυτικών ποσοτήτων
                if sum_type == "Ανά Νούμερο" and size_totals:
                    st.write("**Ποσότητες ανά Νούμερο:**")
                    for size, quantity in size_totals.items():
                        if quantity > 0:
                            st.write(f"- Νούμερο {size}: {quantity} kg")
                
                if sum_type == "Ανά Ποιότητα" and quality_totals:
                    st.write("**Ποσότητες ανά Ποιότητα:**")
                    for quality, quantity in quality_totals.items():
                        if quantity > 0:
                            st.write(f"- Ποιότητα {quality}: {quantity} kg")
            
            # Πίνακας παραγγελιών
            if filtered_orders:
                df = pd.DataFrame(filtered_orders)
                st.dataframe(df[['id', 'date', 'customer', 'total_kg', 'total_value', 'executed_quantity', 'lot']], use_container_width=True)
                
                # Εξαγωγή σε CSV
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Εξαγωγή σε CSV",
                    data=csv_data,
                    file_name=f"orders_report_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Δεν βρέθηκαν παραγγελίες για τα επιλεγμένα κριτήρια")
        
        elif report_type == "Αναφορά Πωλήσεων ανά Πελάτη":
            st.subheader("Αναφορά Πωλήσεων ανά Πελάτη")
            
            customer_sales = {}
            for order in st.session_state['orders']:
                customer_name = order.get('customer', '')
                if customer_name not in customer_sales:
                    customer_sales[customer_name] = {
                        'total_orders': 0,
                        'total_kg': 0,
                        'total_value': 0,
                        'executed_kg': 0
                    }
                
                customer_sales[customer_name]['total_orders'] += 1
                customer_sales[customer_name]['total_kg'] += order['total_kg']
                customer_sales[customer_name]['total_value'] += order['total_value']
                customer_sales[customer_name]['executed_kg'] += order.get('executed_quantity', 0)
            
            if customer_sales:
                df = pd.DataFrame.from_dict(customer_sales, orient='index')
                df.index.name = 'Πελάτης'
                df = df.reset_index()
                
                st.dataframe(df, use_container_width=True)
                
                # Δημιουργία γραφήματος
                fig = px.bar(df, x='Πελάτης', y='total_value', title="Συνολική Αξία Πωλήσεων ανά Πελάτη")
                st.plotly_chart(fig, use_container_width=True)
                
                # Εξαγωγή σε CSV
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Εξαγωγή σε CSV",
                    data=csv_data,
                    file_name="customer_sales_report.csv",
                    mime="text/csv"
                )
            else:
                st.info("Δεν υπάρχουν δεδομένα πωλήσεων")
        
        elif report_type == "Αναφορά Αποθηκευτικών Χώρων":
            st.subheader("Αναφορά Αποθηκευτικών Χώρων")
            
            storage_usage = calculate_storage_usage()
            
            for loc_id, usage in storage_usage.items():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{usage['name']}**")
                    progress = (usage['used'] / usage['capacity']) * 100 if usage['capacity'] > 0 else 0
                    st.progress(min(progress / 100, 1.0))
                
                with col2:
                    st.write(f"Χρησιμοποιημένο: {usage['used']} kg")
                    st.write(f"Συνολική χωρητικότητα: {usage['capacity']} kg")
                
                with col3:
                    st.write(f"Ελεύθερο: {usage['capacity'] - usage['used']} kg")
                    st.write(f"Ποσοστό: {progress:.1f}%")
                
                if usage['items']:
                    with st.expander("Προβολή περιεχομένων"):
                        for item in usage['items']:
                            st.write(f"- Παραλαβή #{item['id']}: {item['kg']} kg ({item['date']}) - {item['producer']}")
                
                st.divider()
        
        elif report_type == "Αναφορά Παραγωγών ανά Παραγγελία":
            st.subheader("Αναφορά Παραγωγών ανά Παραγγελία")
            
            producer_receipts = {}
            for receipt in st.session_state['receipts']:
                producer_name = receipt.get('producer_name', '')
                if producer_name not in producer_receipts:
                    producer_receipts[producer_name] = {
                        'receipts_count': 0,
                        'total_kg': 0,
                        'total_value': 0,
                        'avg_price_per_kg': 0
                    }
                
                producer_receipts[producer_name]['receipts_count'] += 1
                producer_receipts[producer_name]['total_kg'] += receipt['total_kg']
                producer_receipts[producer_name]['total_value'] += receipt['total_value']
            
            # Υπολογισμός μέσης τιμής ανά κιλό
            for producer in producer_receipts.values():
                if producer['total_kg'] > 0:
                    producer['avg_price_per_kg'] = producer['total_value'] / producer['total_kg']
            
            if producer_receipts:
                df = pd.DataFrame.from_dict(producer_receipts, orient='index')
                df.index.name = 'Παραγωγός'
                df = df.reset_index()
                
                st.dataframe(df, use_container_width=True)
                
                # Δημιουργία γραφήματος
                fig = px.bar(df, x='Παραγωγός', y='total_kg', title="Συνολικά Κιλά ανά Παραγωγό")
                st.plotly_chart(fig, use_container_width=True)
                
                # Εξαγωγή σε CSV
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Εξαγωγή σε CSV",
                    data=csv_data,
                    file_name="producer_receipts_report.csv",
                    mime="text/csv"
                )
            else:
                st.info("Δεν υπάρχουν δεδομένα παραγωγών")

# Tab 5: Διαχείριση
def show_management():
    with tabs[4]:
        st.header("⚙️ Διαχείριση Συστήματος")
        
        management_type = st.selectbox("Επιλέξτε τύπο διαχείρισης", [
            "Διαχείριση Παραγωγών",
            "Διαχείριση Πελατών",
            "Διαχείριση Αναφορών"
        ])
        
        if management_type == "Διαχείριση Παραγωγών":
            st.subheader("Διαχείριση Παραγωγών")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Προσθήκη Νέου Παραγωγού**")
                with st.form("add_producer_form"):
                    new_producer_name = st.text_input("Όνομα Παραγωγού")
                    new_producer_quantity = st.number_input("Ποσότητα", min_value=0, step=1)
                    new_producer_certs = st.multiselect(
                        "Πιστοποιήσεις",
                        ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
                    )
                    
                    submitted = st.form_submit_button("➕ Προσθήκη Παραγωγού")
                    
                    if submitted and new_producer_name:
                        new_producer = {
                            "id": get_next_id(st.session_state['producers']),
                            "name": new_producer_name,
                            "quantity": new_producer_quantity,
                            "certifications": new_producer_certs
                        }
                        st.session_state['producers'].append(new_producer)
                        save_data({'producers': st.session_state['producers']})
                        st.success(f"✅ Ο παραγωγός '{new_producer_name}' προστέθηκε επιτυχώς!")
                        time.sleep(1)
                        st.rerun()
            
            with col2:
                st.write("**Υπάρχοντες Παραγωγοί**")
                if st.session_state['producers']:
                    for producer in st.session_state['producers']:
                        with st.expander(f"{producer['id']} - {producer['name']}"):
                            st.write(f"Ποσότητα: {producer['quantity']}")
                            st.write(f"Πιστοποιήσεις: {', '.join(producer.get('certifications', []))}")
                            
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button(f"✏️ Επεξεργασία", key=f"edit_prod_{producer['id']}"):
                                    st.session_state.edit_item = producer
                                    st.session_state.edit_type = 'producers'
                                    st.rerun()
                            with col_del:
                                if can_delete() and st.button(f"🗑️ Διαγραφή", key=f"del_prod_{producer['id']}"):
                                    st.session_state['producers'] = [p for p in st.session_state['producers'] if p['id'] != producer['id']]
                                    save_data({'producers': st.session_state['producers']})
                                    st.success("✅ Διαγραφή επιτυχής!")
                                    time.sleep(1)
                                    st.rerun()
                else:
                    st.info("Δεν υπάρχουν καταχωρημένοι παραγωγοί")
        
        elif management_type == "Διαχείριση Πελατών":
            st.subheader("Διαχείριση Πελατών")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Προσθήκη Νέου Πελάτη**")
                with st.form("add_customer_form"):
                    new_customer_name = st.text_input("Όνομα Πελάτη")
                    new_customer_address = st.text_input("Διεύθυνση")
                    new_customer_phone = st.text_input("Τηλέφωνο")
                    
                    submitted = st.form_submit_button("➕ Προσθήκη Πελάτη")
                    
                    if submitted and new_customer_name:
                        new_customer = {
                            "id": get_next_id(st.session_state['customers']),
                            "name": new_customer_name,
                            "address": new_customer_address,
                            "phone": new_customer_phone
                        }
                        st.session_state['customers'].append(new_customer)
                        save_data({'customers': st.session_state['customers']})
                        st.success(f"✅ Ο πελάτης '{new_customer_name}' προστέθηκε επιτυχώς!")
                        time.sleep(1)
                        st.rerun()
            
            with col2:
                st.write("**Υπάρχοντες Πελάτες**")
                if st.session_state['customers']:
                    for customer in st.session_state['customers']:
                        with st.expander(f"{customer['id']} - {customer['name']}"):
                            st.write(f"Διεύθυνση: {customer['address']}")
                            st.write(f"Τηλέφωνο: {customer['phone']}")
                            
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button(f"✏️ Επεξεργασία", key=f"edit_cust_{customer['id']}"):
                                    st.session_state.edit_item = customer
                                    st.session_state.edit_type = 'customers'
                                    st.rerun()
                            with col_del:
                                if can_delete() and st.button(f"🗑️ Διαγραφή", key=f"del_cust_{customer['id']}"):
                                    st.session_state['customers'] = [c for c in st.session_state['customers'] if c['id'] != customer['id']]
                                    save_data({'customers': st.session_state['customers']})
                                    st.success("✅ Διαγραφή επιτυχής!")
                                    time.sleep(1)
                                    st.rerun()
                else:
                    st.info("Δεν υπάρχουν καταχωρημένοι πελάτες")
        
        elif management_type == "Διαχείριση Αναφορών":
            st.subheader("Διαχείριση Αναφορών")
            
            # Επιλογές για εξαγωγή δεδομένων
            export_type = st.selectbox("Επιλέξτε τύπο δεδομένων για εξαγωγή", [
                "Όλα τα δεδομένα",
                "Παραλαβές",
                "Παραγγελίες",
                "Παραγωγοί",
                "Πελάτες"
            ])
            
            if st.button("📊 Δημιουργία Πλήρους Αναφοράς"):
                # Δημιουργία Excel αρχείου με όλα τα δεδομένα
                with pd.ExcelWriter('full_report.xlsx', engine='openpyxl') as writer:
                    if st.session_state['receipts']:
                        pd.DataFrame(st.session_state['receipts']).to_excel(writer, sheet_name='Παραλαβές', index=False)
                    if st.session_state['orders']:
                        pd.DataFrame(st.session_state['orders']).to_excel(writer, sheet_name='Παραγγελίες', index=False)
                    if st.session_state['producers']:
                        pd.DataFrame(st.session_state['producers']).to_excel(writer, sheet_name='Παραγωγοί', index=False)
                    if st.session_state['customers']:
                        pd.DataFrame(st.session_state['customers']).to_excel(writer, sheet_name='Πελάτες', index=False)
                
                # Ανάγνωση του αρχείου για λήψη
                with open('full_report.xlsx', 'rb') as f:
                    excel_data = f.read()
                
                st.download_button(
                    label="📥 Λήψη Πλήρους Αναφοράς (Excel)",
                    data=excel_data,
                    file_name="full_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Επιλογές για δημιουργία backup
            st.subheader("Δημιουργία Backup")
            
            if st.button("💾 Δημιουργία Backup Συστήματος"):
                backup_data = {
                    'users': st.session_state['users'],
                    'producers': st.session_state['producers'],
                    'customers': st.session_state['customers'],
                    'agencies': st.session_state['agencies'],
                    'receipts': st.session_state['receipts'],
                    'orders': st.session_state['orders'],
                    'storage_locations': st.session_state['storage_locations']
                }
                
                backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
                
                st.download_button(
                    label="📥 Λήψη Backup (JSON)",
                    data=backup_json,
                    file_name=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

# Tab 6: Διαχείριση Χρηστών
def show_user_management():
    with tabs[5]:
        st.header("👥 Διαχείριση Χρηστών")
        
        if st.session_state.user_role != 'admin':
            st.warning("⛔ Μόνο ο διαχειριστής μπορεί να διαχειριστεί χρήστες")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Προσθήκη Νέου Χρήστη")
            with st.form("add_user_form"):
                new_username = st.text_input("Όνομα Χρήστη")
                new_password = st.text_input("Κωδικός Πρόσβασης", type="password")
                new_fullname = st.text_input("Πλήρες Όνομα")
                new_role = st.selectbox("Ρόλος", ["admin", "editor", "viewer"])
                
                submitted = st.form_submit_button("➕ Προσθήκη Χρήστη")
                
                if submitted:
                    if new_username in st.session_state['users']:
                        st.error("❌ Ο χρήστης υπάρχει ήδη")
                    elif new_username and new_password:
                        st.session_state['users'][new_username] = {
                            'password': hash_password(new_password),
                            'role': new_role,
                            'full_name': new_fullname
                        }
                        save_data({'users': st.session_state['users']})
                        st.success(f"✅ Ο χρήστης '{new_username}' προστέθηκε επιτυχώς!")
                        time.sleep(1)
                        st.rerun()
        
        with col2:
            st.subheader("Υπάρχοντες Χρήστες")
            if st.session_state['users']:
                for username, user_data in st.session_state['users'].items():
                    with st.expander(f"{username} ({user_data['role']})"):
                        st.write(f"Πλήρες όνομα: {user_data['full_name']}")
                        
                        if username != st.session_state.current_user:  # Αποτροπή αυτο-διαγραφής
                            if st.button(f"🗑️ Διαγραφή", key=f"del_user_{username}"):
                                del st.session_state['users'][username]
                                save_data({'users': st.session_state['users']})
                                st.success(f"✅ Ο χρήστης '{username}' διαγράφηκε επιτυχώς!")
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.info("Δεν μπορείτε να διαγράψετε τον εαυτό σας")
            else:
                st.info("Δεν υπάρχουν καταχωρημένοι χρήστες")

# Tab 7: Αποθηκευτικοί Χώροι
def show_storage_management():
    with tabs[6]:
        st.header("🏢 Διαχείριση Αποθηκευτικών Χώρων")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Προσθήκη Νέου Αποθηκευτικού Χώρου")
            with st.form("add_storage_form"):
                new_storage_name = st.text_input("Όνομα Αποθήκης")
                new_storage_capacity = st.number_input("Χωρητικότητα (kg)", min_value=1, step=100)
                new_storage_desc = st.text_area("Περιγραφή")
                
                submitted = st.form_submit_button("➕ Προσθήκη Αποθήκης")
                
                if submitted and new_storage_name:
                    new_storage = {
                        "id": get_next_id(st.session_state['storage_locations']),
                        "name": new_storage_name,
                        "capacity": new_storage_capacity,
                        "description": new_storage_desc
                    }
                    st.session_state['storage_locations'].append(new_storage)
                    save_data({'storage_locations': st.session_state['storage_locations']})
                    st.success(f"✅ Η αποθήκη '{new_storage_name}' προστέθηκε επιτυχώς!")
                    time.sleep(1)
                    st.rerun()
        
        with col2:
            st.subheader("Υπάρχοντες Αποθηκευτικοί Χώροι")
            if st.session_state['storage_locations']:
                for storage in st.session_state['storage_locations']:
                    with st.expander(f"{storage['id']} - {storage['name']}"):
                        st.write(f"Χωρητικότητα: {storage['capacity']} kg")
                        st.write(f"Περιγραφή: {storage['description']}")
                        
                        col_edit, col_del = st.columns(2)
                        with col_edit:
                            if st.button(f"✏️ Επεξεργασία", key=f"edit_storage_{storage['id']}"):
                                st.session_state.edit_item = storage
                                st.session_state.edit_type = 'storage_locations'
                                st.rerun()
                        with col_del:
                            if can_delete() and st.button(f"🗑️ Διαγραφή", key=f"del_storage_{storage['id']}"):
                                st.session_state['storage_locations'] = [s for s in st.session_state['storage_locations'] if s['id'] != storage['id']]
                                save_data({'storage_locations': st.session_state['storage_locations']})
                                st.success("✅ Διαγραφή επιτυχής!")
                                time.sleep(1)
                                st.rerun()
            else:
                st.info("Δεν υπάρχουν καταχωρημένοι αποθηκευτικοί χώροι")
        
        # Αναφορά χρήσης αποθηκευτικών χώρων
        st.subheader("📊 Αναφορά Χρήσης Αποθηκευτικών Χώρων")
        
        storage_usage = calculate_storage_usage()
        
        for loc_id, usage in storage_usage.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{usage['name']}**")
                progress = (usage['used'] / usage['capacity']) * 100 if usage['capacity'] > 0 else 0
                st.progress(min(progress / 100, 1.0))
            
            with col2:
                st.write(f"Χρησιμοποιημένο: {usage['used']} kg")
                st.write(f"Συνολική χωρητικότητα: {usage['capacity']} kg")
            
            with col3:
                st.write(f"Ελεύθερο: {usage['capacity'] - usage['used']} kg")
                st.write(f"Ποσοστό: {progress:.1f}%")
            
            if usage['items']:
                with st.expander("Προβολή περιεχομένων"):
                    for item in usage['items']:
                        st.write(f"- Παραλαβή #{item['id']}: {item['kg']} kg ({item['date']}) - {item['producer']}")
            
            st.divider()

# Εμφάνιση της σωστής καρτέλας
show_tab(menu_options.index(selected_menu))

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**Σύστημα Διαχείρισης Παραλαβών & Παραγγελιών**  
🍊 Για τη βιομηχανία εσπεριδοειδών  
v1.0 - © 2024
""")
[file content end]