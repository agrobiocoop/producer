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
            {"id": 2, "name": "Αποθήκη Β", "capacity": 5000, "description": "Δευτερεύουσα αποθήκη"},
            {"id": 3, "name": "Ψυγείο", "capacity": 2000, "description": "Ψυκτική μονάδα"}
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

# Στήλες για το tab layout
tabs = ["Κεντρική Βάση", "Νέα Παραλαβή", "Νέα Παραγγελία", "Αναφορές", "Διαχείριση", "Διαχείριση Χρηστών", "Αποθηκευτικοί Χώροι"]
current_tab = st.tabs(tabs)

# Tab 1: Κεντρική Βάση
with current_tab[0]:
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
            
            # Επιλογή ημερομηνίας - ΔΙΟΡΘΩΜΕΝΟ
            receipt_date = st.date_input("Ημερομηνία Παραλαβής", value=datetime.today())
            
            # Επιλογή παραγωγού
            producer_options = [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
            selected_producer = st.selectbox("Παραγωγός", options=producer_options)
            producer_id = int(selected_producer.split(" - ")[0]) if selected_producer else None
            producer_name = selected_producer.split(" - ")[1] if selected_producer else ""
            
            variety = st.text_input("Ποικιλία")
            
            # Αυτόματη δημιουργία LOT - ΔΙΟΡΘΩΜΕΝΟ
            if variety and producer_id and receipt_date:
                lot_number = generate_lot_number(receipt_date, producer_id, variety)
                st.text_input("Αριθμός LOT", value=lot_number, disabled=True)
            else:
                lot_number = ""
            
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
                size_quantities[size] = st.number_input(f"Ποσότητα για νούμερο {size}", min_value=0, step=1, key=f"size_{size}")
            
            # Πιστοποιήσεις
            certifications = st.multiselect(
                "📑 Πιστοποιήσεις",
                ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
            )
            
            # Συμφωνηθείσα τιμή
            agreed_price_per_kg = st.number_input("💰 Συμφωνηθείσα Τιμή ανά κιλό", min_value=0.0, step=0.01, value=0.0)
            
            # Υπολογισμός συνολικής αξίας
            total_kg = sum(size_quantities.values())
            total_value = total_kg * agreed_price_per_kg if agreed_price_per_kg else 0
            
            if total_kg > 0:
                st.info(f"📦 Σύνολο κιλών: {total_kg} kg")
                st.success(f"💶 Συνολική αξία: {total_value:.2f} €")
            
            observations = st.text_area("📝 Παρατηρήσεις")
        
        submitted = st.form_submit_button("✅ Καταχώρηση Παραλαβής")
        
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
                "certifications": certifications,
                "agreed_price_per_kg": agreed_price_per_kg,
                "total_kg": total_kg,
                "total_value": total_value,
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
                lot_number = generate_lot_number(order_date, customer_id, variety)
                st.text_input("Αριθμός LOT", value=lot_number, disabled=True)
            else:
                lot_number = ""
        
        with col2:
            # Ποσότητες παραγγελίας
            st.subheader("📦 Ποσότητες Παραγγελίας")
            sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
            order_quantities = {}
            for size in sizes:
                order_quantities[size] = st.number_input(f"Ποσότητα για νούμερο {size}", min_value=0, step=1, key=f"order_size_{size}")
            
            # Εκτελεσθείσα ποσότητα - ΝΕΟ ΠΕΔΙΟ
            executed_quantity = st.number_input("Εκτελεσθείσα Ποσότητα (kg)", min_value=0, step=1, value=0)
            
            # Συμφωνηθείσα τιμή
            agreed_price_per_kg = st.number_input("💰 Συμφωνηθείσα Τιμή ανά κιλό", min_value=0.0, step=0.01, value=0.0)
            
            # Υπολογισμός συνολικής αξίας
            total_kg = sum(order_quantities.values())
            total_value = total_kg * agreed_price_per_kg if agreed_price_per_kg else 0
            
            if total_kg > 0:
                st.info(f"📦 Σύνολο κιλών: {total_kg} kg")
                st.success(f"💶 Συνολική αξία: {total_value:.2f} €")
            
            order_observations = st.text_area("📝 Παρατηρήσεις Παραγγελίας")
        
        submitted = st.form_submit_button("✅ Καταχώρηση Παραγγελίας")
        
        if submitted:
            new_order = {
                "id": order_id,
                "date": order_date.strftime("%Y-%m-%d"),
                "customer_id": customer_id,
                "customer": customer_name,
                "variety": variety,
                "lot": lot_number,
                "quantities": order_quantities,
                "executed_quantity": executed_quantity,  # ΝΕΟ ΠΕΔΙΟ
                "agreed_price_per_kg": agreed_price_per_kg,
                "total_kg": total_kg,
                "total_value": total_value,
                "observations": order_observations,
                "created_by": st.session_state.current_user,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.session_state['orders'].append(new_order)
            save_data({'orders': st.session_state['orders']})
            st.success(f"✅ Η παραγγελία #{order_id} καταχωρήθηκε επιτυχώς!")
            time.sleep(2)
            st.rerun()

# Tab 4: Αναφορές
with current_tab[3]:
    st.header("📈 Αναφορές και Εξαγωγές")
    
    report_type = st.selectbox("Επιλέξτε τύπο αναφοράς", [
        "Αναφορά Παραλαβών", 
        "Αναφορά Παραγγελιών", 
        "Αναφορά Πωλήσεων ανά Πελάτη",
        "Αναφορά Αποθηκευτικών Χώρων"
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
            
            total_kg = sum(r['total_kg'] for r in filtered_receipts)
            total_value = sum(r['total_value'] for r in filtered_receipts)
            
            st.metric("Συνολικές Παραλαβές", len(filtered_receipts))
            st.metric("Συνολικά Κιλά", f"{total_kg} kg")
            st.metric("Συνολική Αξία", f"{total_value:.2f} €")
        
        if filtered_receipts:
            df = pd.DataFrame(filtered_receipts)
            st.dataframe(df, use_container_width=True)
            
            # Εξαγωγή σε Excel
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Παραλαβές', index=False)
            
            st.download_button(
                label="📊 Εξαγωγή σε Excel",
                data=excel_buffer.getvalue(),
                file_name=f"αναφορά_παραλαβών_{start_date}_{end_date}.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    elif report_type == "Αναφορά Παραγγελιών":
        st.subheader("Αναφορά Παραγγελιών")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Από ημερομηνία", value=datetime.today() - timedelta(days=30), key="orders_start")
            end_date = st.date_input("Έως ημερομηνία", value=datetime.today(), key="orders_end")
        
        with col2:
            filtered_orders = []
            for order in st.session_state['orders']:
                order_date = datetime.strptime(order['date'], '%Y-%m-%d').date()
                
                if order_date < start_date or order_date > end_date:
                    continue
                
                filtered_orders.append(order)
            
            total_kg = sum(o['total_kg'] for o in filtered_orders)
            total_value = sum(o['total_value'] for o in filtered_orders)
            executed_kg = sum(o.get('executed_quantity', 0) for o in filtered_orders)
            
            st.metric("Συνολικές Παραγγελίες", len(filtered_orders))
            st.metric("Συνολικά Κιλά", f"{total_kg} kg")
            st.metric("Εκτελεσθείσα Ποσότητα", f"{executed_kg} kg")
            st.metric("Συνολική Αξία", f"{total_value:.2f} €")
        
        if filtered_orders:
            df = pd.DataFrame(filtered_orders)
            st.dataframe(df, use_container_width=True)
            
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Παραγγελίες', index=False)
            
            st.download_button(
                label="📊 Εξαγωγή σε Excel",
                data=excel_buffer.getvalue(),
                file_name=f"αναφορά_παραγγελιών_{start_date}_{end_date}.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    elif report_type == "Αναφορά Πωλήσεων ανά Πελάτη":
        st.subheader("Αναφορά Πωλήσεων ανά Πελάτη")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Από ημερομηνία", value=datetime.today() - timedelta(days=90), key="sales_start")
            end_date = st.date_input("Έως ημερομηνία", value=datetime.today(), key="sales_end")
            
            customer_options = ["Όλοι"] + [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
            selected_customer = st.selectbox("Πελάτης", options=customer_options)
        
        with col2:
            customer_sales = {}
            for order in st.session_state['orders']:
                order_date = datetime.strptime(order['date'], '%Y-%m-%d').date()
                
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
            
            # Εμφάνιση αποτελεσμάτων
            for customer, data in customer_sales.items():
                st.write(f"**{customer}**: {data['orders_count']} παραγγελίες, {data['total_kg']} kg, {data['total_value']:.2f}€")
            
            if customer_sales:
                df = pd.DataFrame.from_dict(customer_sales, orient='index')
                df.index.name = 'Πελάτης'
                st.dataframe(df, use_container_width=True)
                
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Πωλήσεις ανά Πελάτη')
                
                st.download_button(
                    label="📊 Εξαγωγή σε Excel",
                    data=excel_buffer.getvalue(),
                    file_name=f"αναφορά_πωλήσεων_πελάτη_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.ms-excel"
                )
    
    else:  # Αναφορά Αποθηκευτικών Χώρων
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
        
        # Εξαγωγή αναφοράς
        df = pd.DataFrame.from_dict(storage_usage, orient='index')
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Αποθηκευτικοί Χώροι')
        
        st.download_button(
            label="📊 Εξαγωγή σε Excel",
            data=excel_buffer.getvalue(),
            file_name="αναφορά_αποθηκευτικών_χώρων.xlsx",
            mime="application/vnd.ms-excel"
        )

# Τα υπόλοιπα tabs παραμένουν όπως στο προηγούμενο μήνυμα
# (Διαχείριση, Διαχείριση Χρηστών, Αποθηκευτικοί Χώροι)

# ... (ο κώδικας για τα υπόλοιπα tabs παραμένει ίδιος με προηγούμενες εκδόσεις)

# Πλευρικό μενού
st.sidebar.header("📋 Γρήγορη Πρόσβαση")
if st.sidebar.button("📊 Εξαγωγή Όλων Δεδομένων"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if st.session_state['producers']:
            pd.DataFrame(st.session_state['producers']).to_excel(writer, sheet_name='Παραγωγοί', index=False)
        if st.session_state['customers']:
            pd.DataFrame(st.session_state['customers']).to_excel(writer, sheet_name='Πελάτες', index=False)
        if st.session_state['receipts']:
            pd.DataFrame(st.session_state['receipts']).to_excel(writer, sheet_name='Παραλαβές', index=False)
        if st.session_state['orders']:
            pd.DataFrame(st.session_state['orders']).to_excel(writer, sheet_name='Παραγγελίες', index=False)
        if st.session_state['storage_locations']:
            pd.DataFrame(st.session_state['storage_locations']).to_excel(writer, sheet_name='Αποθηκευτικοί_Χώροι', index=False)
    
    st.sidebar.download_button(
        label="💾 Κατεβάστε Όλα (Excel)",
        data=output.getvalue(),
        file_name="ολοκληρωμένη_βάση.xlsx",
        mime="application/vnd.ms-excel"
    )

if st.sidebar.button("🔄 Ανανέωση Δεδομένων"):
    data = load_data()
    for key, value in data.items():
        st.session_state[key] = value
    st.sidebar.success("✅ Τα δεδομένα ανανεώθηκαν!")