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
import re

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
if 'view_item' not in st.session_state:
    st.session_state.view_item = None
if 'view_type' not in st.session_state:
    st.session_state.view_type = None

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
    st.session_state.view_item = None
    st.session_state.view_type = None
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

def generate_lot_number(receipt_date, entity_id, variety, is_receipt=True):
    """Αυτόματη δημιουργία αριθμού LOT"""
    date_str = receipt_date.strftime("%y%m%d")
    entity_type = "P" if is_receipt else "C"  # P για Παραγωγό, C για Πελάτη
    variety_code = re.sub(r'[^a-zA-Z0-9]', '', variety)[:3].upper() if variety else "GEN"
    return f"{date_str}-{entity_type}{entity_id}-{variety_code}"

def is_lot_unique(lot_number, current_id=None, is_receipt=True):
    """Έλεγχος αν το LOT είναι μοναδικό"""
    if is_receipt:
        items = st.session_state['receipts']
        key = 'receipts'
    else:
        items = st.session_state['orders']
        key = 'orders'
    
    for item in items:
        if item.get('lot') == lot_number:
            if current_id is None or item['id'] != current_id:
                return False
    return True

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

# Στήλες για το tab layout
tabs = ["Κεντρική Βάση", "Νέα Παραλαβή", "Νέα Παραγγελία", "Αναφορές", "Διαχείριση", "Διαχείριση Χρηστών", "Αποθηκευτικοί Χώροι"]
current_tab = st.tabs(tabs)

# Tab 1: Κεντρική Βάση
with current_tab[0]:
    st.header("📊 Κεντρική Βάση Δεδομένων")
    
    # Επιλογή τύπου δεδομένων για προβολή/επεξεργασία
    data_type = st.selectbox("Επιλέξτε τύπο δεδομένων", ["Παραλαβές", "Παραγγελίες", "Παραγωγοί", "Πελάτες"])
    
    if data_type == "Παραλαβές":
        items = st.session_state['receipts']
        item_key = 'receipts'
        columns = ['id', 'receipt_date', 'producer_name', 'total_kg', 'total_value', 'lot', 'storage_location', 'paid']
    elif data_type == "Παραγγελίες":
        items = st.session_state['orders']
        item_key = 'orders'
        columns = ['id', 'date', 'customer', 'total_kg', 'executed_quantity', 'total_value', 'lot', 'paid']
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
            
            # Επιλογή εγγραφής για προβολή/επεξεργασία/διαγραφή
            options = [f"{item['id']} - {item.get('producer_name', item.get('name', item.get('customer', '')))}" for item in items]
            selected_option = st.selectbox("Επιλέξτε εγγραφή για διαχείριση", options)
            
            if selected_option:
                selected_id = int(selected_option.split(" - ")[0])
                selected_item = next((item for item in items if item['id'] == selected_id), None)
                
                if selected_item:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write("**Λεπτομέρειες Εγγραφής:**")
                        st.json(selected_item)
                    
                    with col2:
                        st.write("**Προβολή:**")
                        if st.button("👁️ Προβολή"):
                            st.session_state.view_item = selected_item
                            st.session_state.view_type = item_key
                            st.rerun()
                    
                    with col3:
                        st.write("**Επεξεργασία:**")
                        if can_edit() and st.button("✏️ Επεξεργασία"):
                            st.session_state.edit_item = selected_item
                            st.session_state.edit_type = item_key
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
with current_tab[1]:
    st.header("📥 Καταχώρηση Νέας Παραλαβής")
    
    with st.form("receipt_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            receipt_id = st.number_input("Αριθμός Παραλαβής", min_value=1, step=1, value=get_next_id(st.session_state['receipts']))
            
            # Επιλογή ημερομηνίας
            receipt_date = st.date_input("Ημερομηνία Παραλαβής", value=datetime.today())
            
            # Επιλογή παραγωγού
            producer_options = [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
            selected_producer = st.selectbox("Παραγωγός", options=producer_options)
            producer_id = int(selected_producer.split(" - ")[0]) if selected_producer else None
            producer_name = selected_producer.split(" - ")[1] if selected_producer else ""
            
            variety = st.text_input("Ποικιλία")
            
            # Αυτόματη δημιουργία LOT
            if variety and producer_id and receipt_date:
                lot_number = generate_lot_number(receipt_date, producer_id, variety, is_receipt=True)
                # Έλεγχος μοναδικότητας LOT
                if not is_lot_unique(lot_number, is_receipt=True):
                    st.error("⚠️ Το LOT υπάρχει ήδη! Αλλάξτε ποικιλία ή ημερομηνία")
                st.text_input("Αριθμός LOT", value=lot_number, disabled=True)
            else:
                lot_number = ""
                st.text_input("Αριθμός LOT", value="", disabled=True)
            
            # Επιλογή αποθηκευτικού χώρου
            storage_options = [f"{s['id']} - {s['name']}" for s in st.session_state['storage_locations']]
            selected_storage = st.selectbox("Αποθηκευτικός Χώρος", options=storage_options)
            storage_id = int(selected_storage.split(" - ")[0]) if selected_storage else None
        
        with col2:
            # Ποσότητες ανά νούμερο
            st.subheader("📊 Ποσότητες ανά Νούμερο")
            sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
            size_quantities = {}
            for size in sizes:
                size_quantities[size] = st.number_input(f"Ποσότητα για νούμερο {size}", min_value=0, step=1, key=f"size_{size}", value=0)
            
            # ΠΟΙΟΤΗΤΕΣ (ΣΚΑΡΤΑ)
            st.subheader("📊 Ποιότητες (Σκάρτα)")
            qualities = ["I", "II", "III"]
            quality_quantities = {}
            for quality in qualities:
                quality_quantities[quality] = st.number_input(f"Ποσότητα για ποιότητα {quality}", min_value=0, step=1, key=f"quality_{quality}", value=0)
            
            # Πιστοποιήσεις
            certifications = st.multiselect(
                "📑 Πιστοποιήσεις",
                ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
            )
            
            # Συμφωνηθείσα τιμή
            agreed_price_per_kg = st.number_input("💰 Συμφωνηθείσα Τιμή ανά κιλό", min_value=0.0, step=0.01, value=0.0)
            
            # Πληρώθηκε;
            paid = st.selectbox("💶 Πληρώθηκε;", ["Ναι", "Όχι"], index=1)
            
            # Υπολογισμός συνολικής αξίας
            total_kg = sum(size_quantities.values()) + sum(quality_quantities.values())
            total_value = total_kg * agreed_price_per_kg if agreed_price_per_kg else 0
            
            if total_kg > 0:
                st.info(f"📦 Σύνολο κιλών: {total_kg} kg")
                st.success(f"💶 Συνολική αξία: {total_value:.2f} €")
            
            observations = st.text_area("📝 Παρατηρήσεις")
        
        submitted = st.form_submit_button("✅ Καταχώρηση Παραλαβής")
        
        if submitted:
            if not variety or not producer_id:
                st.error("Παρακαλώ συμπληρώστε ποικιλία και παραγωγό")
            elif not is_lot_unique(lot_number, is_receipt=True):
                st.error("Το LOT υπάρχει ήδη! Αλλάξτε ποικιλία ή ημερομηνία")
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
                    "quality_quantities": quality_quantities,  # Νέο πεδίο ποιοτήτων
                    "certifications": certifications,
                    "agreed_price_per_kg": agreed_price_per_kg,
                    "total_kg": total_kg,
                    "total_value": total_value,
                    "paid": paid,
                    "observations": observations,
                    "created_by": st.session_state.current_user,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.session_state['receipts'].append(new_receipt)
                save_data({'receipts': st.session_state['receipts']})
                st.success(f"✅ Η παραλαβή #{receipt_id} καταχωρήθηκε επιτυχώς!")
                time.sleep(2)
                st.rerun()

# Tab 3: Νέα Παραγγελία
with current_tab[2]:
    st.header("📋 Καταχώρηση Νέας Παραγγελίας")
    
    with st.form("order_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            order_id = st.number_input("Αριθμός Παραγγελίας", min_value=1, step=1, value=get_next_id(st.session_state['orders']))
            
            order_date = st.date_input("Ημερομηνία Παραγγελίας", value=datetime.today())
            
            # Επιλογή πελάτη
            customer_options = [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
            selected_customer = st.selectbox("Πελάτης", options=customer_options)
            customer_id = int(selected_customer.split(" - ")[0]) if selected_customer else None
            customer_name = selected_customer.split(" - ")[1] if selected_customer else ""
            
            variety = st.text_input("Ποικιλία Παραγγελίας")
            
            # Αυτόματη δημιουργία LOT
            if variety and customer_id and order_date:
                lot_number = generate_lot_number(order_date, customer_id, variety, is_receipt=False)
                # Έλεγχος μοναδικότητας LOT
                if not is_lot_unique(lot_number, is_receipt=False):
                    st.error("⚠️ Το LOT υπάρχει ήδη! Αλλάξτε ποικιλία ή ημερομηνία")
                st.text_input("Αριθμός LOT", value=lot_number, disabled=True)
            else:
                lot_number = ""
                st.text_input("Αριθμός LOT", value="", disabled=True)
        
        with col2:
            # Ποσότητες παραγγελίας - ΔΥΟ ΠΟΣΟΤΗΤΕΣ
            st.subheader("📦 Ποσότητες Παραγγελίας")
            
            # ΠΟΣΟΤΗΤΑ 1: Παραγγελθείσα
            st.write("**Παραγγελθείσα Ποσότητα:**")
            sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
            ordered_quantities = {}
            for size in sizes:
                ordered_quantities[size] = st.number_input(f"Παραγγελθείσα για νούμερο {size}", min_value=0, step=1, key=f"ordered_{size}", value=0)
            
            # ΠΟΣΟΤΗΤΑ 2: Παραδοθείσα
            st.write("**Παραδοθείσα Ποσότητα:**")
            delivered_quantities = {}
            for size in sizes:
                delivered_quantities[size] = st.number_input(f"Παραδοθείσα για νούμερο {size}", min_value=0, step=1, value=0, key=f"delivered_{size}", value=0)
            
            # ΠΟΙΟΤΗΤΕΣ (ΣΚΑΡΤΑ)
            st.subheader("📊 Ποιότητες (Σκάρτα)")
            qualities = ["I", "II", "III"]
            quality_quantities = {}
            for quality in qualities:
                quality_quantities[quality] = st.number_input(f"Ποσότητα για ποιότητα {quality}", min_value=0, step=1, key=f"quality_order_{quality}", value=0)
            
            # Συμφωνηθείσα τιμή
            agreed_price_per_kg = st.number_input("💰 Συμφωνηθείσα Τιμή ανά κιλό", min_value=0.0, step=0.01, value=0.0)
            
            # Πληρώθηκε;
            paid = st.selectbox("💶 Πληρώθηκε;", ["Ναι", "Όχι"], index=1)
            
            # Υπολογισμός συνολικών ποσοτήτων
            total_ordered_kg = sum(ordered_quantities.values()) + sum(quality_quantities.values())
            total_delivered_kg = sum(delivered_quantities.values()) + sum(quality_quantities.values())
            total_value = total_delivered_kg * agreed_price_per_kg if agreed_price_per_kg else 0
            
            if total_ordered_kg > 0:
                st.info(f"📦 Σύνολο παραγγελθέντων: {total_ordered_kg} kg")
            if total_delivered_kg > 0:
                st.success(f"📦 Σύνολο παραδοθέντων: {total_delivered_kg} kg")
                st.success(f"💶 Συνολική αξία: {total_value:.2f} €")
            
            order_observations = st.text_area("📝 Παρατηρήσεις Παραγγελίας")
        
        submitted = st.form_submit_button("✅ Καταχώρηση Παραγγελίας")
        
        if submitted:
            if not variety or not customer_id:
                st.error("Παρακαλώ συμπληρώστε ποικιλία και πελάτη")
            elif not is_lot_unique(lot_number, is_receipt=False):
                st.error("Το LOT υπάρχει ήδη! Αλλάξτε ποικιλία ή ημερομηνία")
            else:
                new_order = {
                    "id": order_id,
                    "date": order_date.strftime("%Y-%m-%d"),
                    "customer_id": customer_id,
                    "customer": customer_name,
                    "variety": variety,
                    "lot": lot_number,
                    "ordered_quantities": ordered_quantities,  # Παραγγελθείσες ποσότητες
                    "delivered_quantities": delivered_quantities,  # Παραδοθείσες ποσότητες
                    "quality_quantities": quality_quantities,  # Νέο πεδίο ποιοτήτων
                    "total_ordered_kg": total_ordered_kg,  # Σύνολο παραγγελθέντων
                    "total_delivered_kg": total_delivered_kg,  # Σύνολο παραδοθέντων
                    "agreed_price_per_kg": agreed_price_per_kg,
                    "total_value": total_value,
                    "paid": paid,
                    "observations": order_observations,
                    "created_by": st.session_state.current_user,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.session_state['orders'].append(new_order)
                save_data({'orders': st.session_state['orders']})
                st.success(f"✅ Η παραγγελία #{order_id} καταχωρήθηκε επιτυχώς!")
                time.sleep(2)
                st.rerun()

# ... (Οι υπόλοιποι tabs παραμένουν όπως πριν - Αναφορές, Διαχείριση, Διαχείριση Χρηστών, Αποθηκευτικοί Χώροι)

# Προβολή/Επεξεργασία Εγγραφών
if st.session_state.view_item or st.session_state.edit_item:
    st.header("👁️ Προβολή/Επεξεργασία Εγγραφής")
    
    if st.session_state.edit_item:
        item = st.session_state.edit_item
        item_type = st.session_state.edit_type
        is_edit = True
    else:
        item = st.session_state.view_item
        item_type = st.session_state.view_type
        is_edit = False
    
    if item and item_type:
        with st.form("edit_form"):
            st.write(f"### {'Επεξεργασία' if is_edit else 'Προβολή'} {item_type[:-1]} #{item['id']}")
            
            if item_type == 'receipts':
                # Επεξεργασία Παραλαβής
                receipt_date = st.date_input("Ημερομηνία Παραλαβής", 
                                           value=datetime.strptime(item['receipt_date'], '%Y-%m-%d').date(),
                                           disabled=not is_edit)
                
                producer_options = [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
                selected_producer = st.selectbox("Παραγωγός", options=producer_options,
                                               index=next((i for i, p in enumerate(producer_options) if p.startswith(f"{item['producer_id']} -")), 0),
                                               disabled=not is_edit)
                
                variety = st.text_input("Ποικιλία", value=item.get('variety', ''), disabled=not is_edit)
                lot = st.text_input("LOT", value=item.get('lot', ''), disabled=not is_edit)
                
                # Ποσότητες
                st.subheader("Ποσότητες ανά Νούμερο")
                sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
                size_quantities = item.get('size_quantities', {})
                
                for size in sizes:
                    size_quantities[size] = st.number_input(
                        f"Ποσότητα για νούμερο {size}", 
                        value=size_quantities.get(size, 0),
                        min_value=0, step=1, 
                        disabled=not is_edit,
                        key=f"edit_size_{size}"
                    )
                
                # Ποιότητες (Σκάρτα)
                st.subheader("Ποιότητες (Σκάρτα)")
                qualities = ["I", "II", "III"]
                quality_quantities = item.get('quality_quantities', {})
                
                for quality in qualities:
                    quality_quantities[quality] = st.number_input(
                        f"Ποσότητα για ποιότητα {quality}", 
                        value=quality_quantities.get(quality, 0),
                        min_value=0, step=1, 
                        disabled=not is_edit,
                        key=f"edit_quality_{quality}"
                    )
                
                total_kg = sum(size_quantities.values()) + sum(quality_quantities.values())
                st.info(f"📦 Σύνολο κιλών: {total_kg} kg")
                
                # Πληρώθηκε;
                paid_options = ["Ναι", "Όχι"]
                paid_index = paid_options.index(item.get('paid', 'Όχι'))
                paid = st.selectbox("Πληρώθηκε", options=paid_options, index=paid_index, disabled=not is_edit)
                
            elif item_type == 'orders':
                # Επεξεργασία Παραγγελίας
                order_date = st.date_input("Ημερομηνία Παραγγελίας", 
                                         value=datetime.strptime(item['date'], '%Y-%m-%d').date(),
                                         disabled=not is_edit)
                
                customer_options = [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
                selected_customer = st.selectbox("Πελάτης", options=customer_options,
                                               index=next((i for i, c in enumerate(customer_options) if c.startswith(f"{item['customer_id']} -")), 0),
                                               disabled=not is_edit)
                
                variety = st.text_input("Ποικιλία", value=item.get('variety', ''), disabled=not is_edit)
                lot = st.text_input("LOT", value=item.get('lot', ''), disabled=not is_edit)
                
                # ΔΥΟ ΠΟΣΟΤΗΤΕΣ: Παραγγελθείσα και Παραδοθείσα
                st.subheader("Ποσότητες Παραγγελίας")
                sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
                
                # Παραγγελθείσες ποσότητες
                st.write("**Παραγγελθείσες Ποσότητες:**")
                ordered_quantities = item.get('ordered_quantities', {})
                for size in sizes:
                    ordered_quantities[size] = st.number_input(
                        f"Παραγγελθείσα για {size}", 
                        value=ordered_quantities.get(size, 0),
                        min_value=0, step=1,
                        disabled=not is_edit,
                        key=f"edit_ordered_{size}"
                    )
                
                # Παραδοθείσες ποσότητες
                st.write("**Παραδοθείσες Ποσότητες:**")
                delivered_quantities = item.get('delivered_quantities', {})
                for size in sizes:
                    delivered_quantities[size] = st.number_input(
                        f"Παραδοθείσα για {size}", 
                        value=delivered_quantities.get(size, 0),
                        min_value=0, step=1,
                        disabled=not is_edit,
                        key=f"edit_delivered_{size}"
                    )
                
                # Ποιότητες (Σκάρτα)
                st.subheader("Ποιότητες (Σκάρτα)")
                qualities = ["I", "II", "III"]
                quality_quantities = item.get('quality_quantities', {})
                
                for quality in qualities:
                    quality_quantities[quality] = st.number_input(
                        f"Ποσότητα για ποιότητα {quality}", 
                        value=quality_quantities.get(quality, 0),
                        min_value=0, step=1,
                        disabled=not is_edit,
                        key=f"edit_quality_order_{quality}"
                    )
                
                total_ordered = sum(ordered_quantities.values()) + sum(quality_quantities.values())
                total_delivered = sum(delivered_quantities.values()) + sum(quality_quantities.values())
                
                st.info(f"📦 Σύνολο παραγγελθέντων: {total_ordered} kg")
                st.success(f"📦 Σύνολο παραδοθέντων: {total_delivered} kg")
                
                # Πληρώθηκε;
                paid_options = ["Ναι", "Όχι"]
                paid_index = paid_options.index(item.get('paid', 'Όχι'))
                paid = st.selectbox("Πληρώθηκε", options=paid_options, index=paid_index, disabled=not is_edit)
            
            # Κουμπιά actions
            col1, col2 = st.columns(2)
            
            with col1:
                if is_edit and st.form_submit_button("💾 Αποθήκευση Αλλαγών"):
                    # Ενημέρωση του αντικειμένου
                    if item_type == 'receipts':
                        item.update({
                            'receipt_date': receipt_date.strftime('%Y-%m-%d'),
                            'producer_id': int(selected_producer.split(" - ")[0]),
                            'producer_name': selected_producer.split(" - ")[1],
                            'variety': variety,
                            'lot': lot,
                            'size_quantities': size_quantities,
                            'quality_quantities': quality_quantities,
                            'total_kg': total_kg,
                            'paid': paid
                        })
                    elif item_type == 'orders':
                        item.update({
                            'date': order_date.strftime('%Y-%m-%d'),
                            'customer_id': int(selected_customer.split(" - ")[0]),
                            'customer': selected_customer.split(" - ")[1],
                            'variety': variety,
                            'lot': lot,
                            'ordered_quantities': ordered_quantities,
                            'delivered_quantities': delivered_quantities,
                            'quality_quantities': quality_quantities,
                            'total_ordered_kg': total_ordered,
                            'total_delivered_kg': total_delivered,
                            'paid': paid
                        })
                    
                    # Αποθήκευση
                    save_data({item_type: st.session_state[item_type]})
                    st.success("✅ Οι αλλαγές αποθηκεύτηκαν!")
                    time.sleep(1)
                    st.session_state.edit_item = None
                    st.session_state.edit_type = None
                    st.rerun()
            
            with col2:
                if st.form_submit_button("❌ Έξοδος"):
                    st.session_state.view_item = None
                    st.session_state.view_type = None
                    st.session_state.edit_item = None
                    st.session_state.edit_type = None
                    st.rerun()

# ... (Οι υπόλοιποι tabs παραμένουν όπως πριν)

# Πλευρικό μενού
st.sidebar.header("📋 Γρήγορη Πρόσβαση")
if st.sidebar.button("📊 Εξαγωγή Όλων Δεδομένων (CSV)"):
    # Εξαγωγή όλων των δεδομένων σε CSV
    csv_data = ""
    
    # Παραγωγοί
    if st.session_state['producers']:
        producers_df = pd.DataFrame(st.session_state['producers'])
        csv_data += "ΠΑΡΑΓΩΓΟΙ\n"
        csv_data += producers_df.to_csv(index=False)
        csv_data += "\n\n"
    
    # Πελάτες
    if st.session_state['customers']:
        customers_df = pd.DataFrame(st.session_state['customers'])
        csv_data += "ΠΕΛΑΤΕΣ\n"
        csv_data += customers_df.to_csv(index=False)
        csv_data += "\n\n"
    
    # Παραλαβές
    if st.session_state['receipts']:
        receipts_df = pd.DataFrame(st.session_state['receipts'])
        csv_data += "ΠΑΡΑΛΑΒΕΣ\n"
        csv_data += receipts_df.to_csv(index=False)
        csv_data += "\n\n"
    
    # Παραγγελίες
    if st.session_state['orders']:
        orders_df = pd.DataFrame(st.session_state['orders'])
        csv_data += "ΠΑΡΑΓΓΕΛΙΕΣ\n"
        csv_data += orders_df.to_csv(index=False)
    
    st.sidebar.download_button(
        label="💾 Κατεβάστε Όλα (CSV)",
        data=csv_data.encode('utf-8'),
        file_name="ολοκληρωμένη_βάση.csv",
        mime="text/csv"
    )

if st.sidebar.button("🔄 Ανανέωση Δεδομένων"):
    data = load_data()
    for key, value in data.items():
        st.session_state[key] = value
    st.sidebar.success("✅ Τα δεδομένα ανανεώθηκαν!")