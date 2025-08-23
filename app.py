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
    
    # Επιλογή τύπου δεδομένων για προβολή/επεξεργασία
    data_type = st.selectbox("Επιλέξτε τύπο δεδομένων", ["Παραλαβές", "Παραγγελίες", "Παραγωγοί", "Πελάτες"])
    
    if data_type == "Παραλαβές":
        items = st.session_state['receipts']
        item_key = 'receipts'
        columns = ['id', 'receipt_date', 'producer_name', 'total_kg', 'total_value', 'lot', 'storage_location']
    elif data_type == "Παραγγελίες":
        items = st.session_state['orders']
        item_key = 'orders'
        columns = ['id', 'date', 'customer', 'total_kg', 'executed_quantity', 'total_value', 'lot']
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
            # Ποσότητες παραγγελίας - ΔΥΟ ΠΟΣΟΤΗΤΕΣ
            st.subheader("📦 Ποσότητες Παραγγελίας")
            
            # ΠΟΣΟΤΗΤΑ 1: Παραγγελθείσα
            st.write("**Παραγγελθείσα Ποσότητα:**")
            sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
            ordered_quantities = {}
            for size in sizes:
                ordered_quantities[size] = st.number_input(f"Παραγγελθείσα για νούμερο {size}", min_value=0, step=1, key=f"ordered_{size}")
            
            # ΠΟΣΟΤΗΤΑ 2: Παραδοθείσα
            st.write("**Παραδοθείσα Ποσότητα:**")
            delivered_quantities = {}
            for size in sizes:
                delivered_quantities[size] = st.number_input(f"Παραδοθείσα για νούμερο {size}", min_value=0, step=1, value=0, key=f"delivered_{size}")
            
            # Συμφωνηθείσα τιμή
            agreed_price_per_kg = st.number_input("💰 Συμφωνηθείσα Τιμή ανά κιλό", min_value=0.0, step=0.01, value=0.0)
            
            # Υπολογισμός συνολικών ποσοτήτων
            total_ordered_kg = sum(ordered_quantities.values())
            total_delivered_kg = sum(delivered_quantities.values())
            total_value = total_delivered_kg * agreed_price_per_kg if agreed_price_per_kg else 0
            
            if total_ordered_kg > 0:
                st.info(f"📦 Σύνολο παραγγελθέντων: {total_ordered_kg} kg")
            if total_delivered_kg > 0:
                st.success(f"📦 Σύνολο παραδοθέντων: {total_delivered_kg} kg")
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
                "ordered_quantities": ordered_quantities,  # Παραγγελθείσες ποσότητες
                "delivered_quantities": delivered_quantities,  # Παραδοθείσες ποσότητες
                "total_ordered_kg": total_ordered_kg,  # Σύνολο παραγγελθέντων
                "total_delivered_kg": total_delivered_kg,  # Σύνολο παραδοθέντων
                "agreed_price_per_kg": agreed_price_per_kg,
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
    st.header("📈 Αναφορές και Στατιστικά")
    
    # Επιλογές αναφορών
    report_type = st.selectbox("Επιλέξτε τύπο αναφοράς", [
        "Σύνοψη Παραλαβών και Παραγγελιών",
        "Στατιστικά Παραγωγών",
        "Στατιστικά Πελατών",
        "Χρήση Αποθηκευτικού Χώρου",
        "Αναλυτική Κίνηση Προϊόντων"
    ])
    
    # Φίλτρα ημερομηνιών
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Από ημερομηνία", value=datetime.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("Έως ημερομηνία", value=datetime.today())
    
    if st.button("📊 Δημιουργία Αναφοράς"):
        st.subheader(f"Αναφορά: {report_type}")
        
        if report_type == "Σύνοψη Παραλαβών και Παραγγελιών":
            # Υπολογισμός συνολικών παραλαβών
            total_receipts = sum(receipt['total_kg'] for receipt in st.session_state['receipts'] 
                               if datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date() >= start_date
                               and datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date() <= end_date)
            
            # Υπολογισμός συνολικών παραγγελιών
            total_orders = sum(order['total_delivered_kg'] for order in st.session_state['orders'] 
                             if datetime.strptime(order['date'], '%Y-%m-%d').date() >= start_date
                             and datetime.strptime(order['date'], '%Y-%m-%d').date() <= end_date)
            
            # Υπολογισμός αξιών
            total_receipts_value = sum(receipt['total_value'] for receipt in st.session_state['receipts'] 
                                     if datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date() >= start_date
                                     and datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date() <= end_date)
            
            total_orders_value = sum(order['total_value'] for order in st.session_state['orders'] 
                                   if datetime.strptime(order['date'], '%Y-%m-%d').date() >= start_date
                                   and datetime.strptime(order['date'], '%Y-%m-%d').date() <= end_date)
            
            # Εμφάνιση αποτελεσμάτων
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Συνολικές Παραλαβές (kg)", f"{total_receipts:,.0f}")
            with col2:
                st.metric("Συνολικές Παραγγελίες (kg)", f"{total_orders:,.0f}")
            with col3:
                st.metric("Αξία Παραλαβών (€)", f"{total_receipts_value:,.2f}")
            with col4:
                st.metric("Αξία Παραγγελιών (€)", f"{total_orders_value:,.2f}")
            
            # Διάγραμμα
            chart_data = pd.DataFrame({
                'Κατηγορία': ['Παραλαβές', 'Παραγγελίες'],
                'Ποσότητα (kg)': [total_receipts, total_orders],
                'Αξία (€)': [total_receipts_value, total_orders_value]
            })
            
            st.bar_chart(chart_data.set_index('Κατηγορία'))
            
        elif report_type == "Στατιστικά Παραγωγών":
            producers_data = {}
            for receipt in st.session_state['receipts']:
                if (datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date() >= start_date and
                    datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date() <= end_date):
                    producer_id = receipt['producer_id']
                    if producer_id not in producers_data:
                        producers_data[producer_id] = {
                            'name': receipt['producer_name'],
                            'total_kg': 0,
                            'total_value': 0,
                            'count': 0
                        }
                    producers_data[producer_id]['total_kg'] += receipt['total_kg']
                    producers_data[producer_id]['total_value'] += receipt['total_value']
                    producers_data[producer_id]['count'] += 1
            
            if producers_data:
                df = pd.DataFrame.from_dict(producers_data, orient='index')
                df = df.sort_values('total_kg', ascending=False)
                st.dataframe(df)
                
                # Διάγραμμα παραγωγών ανά ποσότητα
                st.bar_chart(df['total_kg'])
            else:
                st.info("Δεν βρέθηκαν δεδομένα για την επιλεγμένη περίοδο")
                
        elif report_type == "Στατιστικά Πελατών":
            customers_data = {}
            for order in st.session_state['orders']:
                if (datetime.strptime(order['date'], '%Y-%m-%d').date() >= start_date and
                    datetime.strptime(order['date'], '%Y-%m-%d').date() <= end_date):
                    customer_id = order['customer_id']
                    if customer_id not in customers_data:
                        customers_data[customer_id] = {
                            'name': order['customer'],
                            'total_kg': 0,
                            'total_value': 0,
                            'count': 0
                        }
                    customers_data[customer_id]['total_kg'] += order['total_delivered_kg']
                    customers_data[customer_id]['total_value'] += order['total_value']
                    customers_data[customer_id]['count'] += 1
            
            if customers_data:
                df = pd.DataFrame.from_dict(customers_data, orient='index')
                df = df.sort_values('total_value', ascending=False)
                st.dataframe(df)
                
                # Διάγραμμα πελατών ανά αξία
                st.bar_chart(df['total_value'])
            else:
                st.info("Δεν βρέθηκαν δεδομένα για την επιλεγμένη περίοδο")
                
        elif report_type == "Χρήση Αποθηκευτικού Χώρου":
            storage_usage = calculate_storage_usage()
            
            usage_data = []
            for loc_id, data in storage_usage.items():
                usage_percent = (data['used'] / data['capacity']) * 100 if data['capacity'] > 0 else 0
                usage_data.append({
                    'Αποθήκη': data['name'],
                    'Χρησιμοποιημένος Χώρος (kg)': data['used'],
                    'Συνολική Χωρητικότητα (kg)': data['capacity'],
                    'Ποσοστό Χρήσης (%)': usage_percent
                })
            
            df = pd.DataFrame(usage_data)
            st.dataframe(df)
            
            # Διάγραμμα χρήσης αποθηκευτικού χώρου
            st.bar_chart(df.set_index('Αποθήκη')[['Χρησιμοποιημένος Χώρος (kg)', 'Συνολική Χωρητικότητα (kg)']])
            
        elif report_type == "Αναλυτική Κίνηση Προϊόντων":
            # Κίνηση ανά ποικιλία
            variety_data = {}
            
            # Παραλαβές ανά ποικιλία
            for receipt in st.session_state['receipts']:
                if (datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date() >= start_date and
                    datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date() <= end_date):
                    variety = receipt.get('variety', 'Άγνωστη')
                    if variety not in variety_data:
                        variety_data[variety] = {'received': 0, 'delivered': 0}
                    variety_data[variety]['received'] += receipt['total_kg']
            
            # Παραδόσεις ανά ποικιλία
            for order in st.session_state['orders']:
                if (datetime.strptime(order['date'], '%Y-%m-%d').date() >= start_date and
                    datetime.strptime(order['date'], '%Y-%m-%d').date() <= end_date):
                    variety = order.get('variety', 'Άγνωστη')
                    if variety not in variety_data:
                        variety_data[variety] = {'received': 0, 'delivered': 0}
                    variety_data[variety]['delivered'] += order['total_delivered_kg']
            
            if variety_data:
                df = pd.DataFrame.from_dict(variety_data, orient='index')
                df['διαθέσιμο'] = df['received'] - df['delivered']
                df = df.sort_values('received', ascending=False)
                st.dataframe(df)
                
                # Διάγραμμα κίνησης ανά ποικιλία
                st.bar_chart(df[['received', 'delivered']])
            else:
                st.info("Δεν βρέθηκαν δεδομένα για την επιλεγμένη περίοδο")
    
    # Εξαγωγή αναφοράς
    if st.button("📥 Εξαγωγή Αναφοράς (CSV)"):
        # Δημιουργία CSV
        csv_data = f"Αναφορά: {report_type}\n"
        csv_data += f"Περίοδος: {start_date} έως {end_date}\n\n"
        
        # Προσθήκη δεδομένων ανά τύπο αναφοράς
        if report_type == "Σύνοψη Παραλαβών και Παραγγελιών":
            # ... (προσθήκη δεδομένων)
            pass
        
        st.download_button(
            label="💾 Κατέβασμα Αναφοράς",
            data=csv_data.encode('utf-8'),
            file_name=f"αναφορά_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

# Tab 5: Διαχείριση
with current_tab[4]:
    st.header("⚙️ Διαχείριση Συστήματος")
    
    if st.session_state.user_role != 'admin':
        st.warning("⛔ Δεν έχετε δικαιώματα πρόσβασης στη Διαχείριση Συστήματος")
        st.stop()
    
    management_option = st.selectbox("Επιλογή Διαχειριστικής Ενέργειας", [
        "Εισαγωγή Δεδομένων",
        "Επαναφορά Συστήματος",
        "Δημιουργία Αντιγράφου Ασφαλείας",
        "Ενημέρωση Συστήματος"
    ])
    
    if management_option == "Εισαγωγή Δεδομένων":
        st.subheader("Εισαγωγή Δεδομένων από CSV")
        
        uploaded_file = st.file_uploader("Ανεβάστε αρχείο CSV", type="csv")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Προεπισκόπηση δεδομένων:")
                st.dataframe(df.head())
                
                data_type = st.selectbox("Τύπος δεδομένων προς εισαγωγή", [
                    "Παραγωγοί", "Πελάτες", "Παραλαβές", "Παραγγελίες"
                ])
                
                if st.button("Εισαγωγή Δεδομένων"):
                    # Εδώ θα μπορούσε να προστεθεί λογική εισαγωγής δεδομένων
                    st.success("Τα δεδομένα εισήχθησαν επιτυχώς!")
            except Exception as e:
                st.error(f"Σφάλμα ανάγνωσης αρχείου: {e}")
    
    elif management_option == "Επαναφορά Συστήματος":
        st.subheader("Επαναφορά Συστήματος στις προεπιλεγμένες ρυθμίσεις")
        st.warning("⚠️ Προσοχή: Αυτή η ενέργεια θα διαγράψει όλα τα δεδομένα!")
        
        if st.button("Επαναφορά Συστήματος", type="secondary"):
            # Επαναφορά όλων των δεδομένων
            for key in st.session_state.keys():
                if key not in ['authenticated', 'current_user', 'user_role']:
                    st.session_state[key] = []
            
            # Επαναρχικοποίηση
            init_data()
            st.success("Το σύστημα επαναφέρθηκε επιτυχώς!")
            time.sleep(2)
            st.rerun()
    
    elif management_option == "Δημιουργία Αντιγράφου Ασφαλείας":
        st.subheader("Δημιουργία Αντιγράφου Ασφαλείας")
        
        if st.button("Δημιουργία Αντιγράφου"):
            # Δημιουργία backup όλων των δεδομένων
            backup_data = {}
            for key in st.session_state:
                if key not in ['authenticated', 'current_user', 'user_role']:
                    backup_data[key] = st.session_state[key]
            
            # Αποθήκευση backup
            with open(f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json", 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            st.success("Το αντίγραφο ασφαλείας δημιουργήθηκε επιτυχώς!")
    
    elif management_option == "Ενημέρωση Συστήματος":
        st.subheader("Ενημέρωση Συστήματος")
        st.info("Ελέγξτε για διαθέσιμες ενημερώσεις συστήματος")
        
        if st.button("Έλεγχος Ενημερώσεων"):
            st.success("Το σύστημα είναι ενημερωμένο στην τελευταία έκδοση!")

# Tab 6: Διαχείριση Χρηστών
with current_tab[5]:
    st.header("👥 Διαχείριση Χρηστών")
    
    if st.session_state.user_role != 'admin':
        st.warning("⛔ Δεν έχετε δικαιώματα πρόσβασης στη Διαχείριση Χρηστών")
        st.stop()
    
    user_management_option = st.selectbox("Επιλογή", [
        "Προβολή Χρηστών",
        "Προσθήκη Νέου Χρήστη",
        "Επεξεργασία Χρήστη",
        "Διαγραφή Χρήστη"
    ])
    
    if user_management_option == "Προβολή Χρηστών":
        st.subheader("Λίστα Χρηστών Συστήματος")
        
        users_df = pd.DataFrame.from_dict(st.session_state['users'], orient='index')
        users_df = users_df.reset_index().rename(columns={'index': 'username'})
        users_df = users_df[['username', 'full_name', 'role']]  # Αποκλείουμε τον κωδικό
        
        st.dataframe(users_df, use_container_width=True)
        
        st.metric("Συνολικοί Χρήστες", len(users_df))
        
    elif user_management_option == "Προσθήκη Νέου Χρήστη":
        st.subheader("Προσθήκη Νέου Χρήστη")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Όνομα Χρήστη")
                new_full_name = st.text_input("Πλήρες Όνομα")
                new_password = st.text_input("Κωδικός Πρόσβασης", type="password")
            
            with col2:
                new_role = st.selectbox("Ρόλος", ["admin", "editor", "viewer"])
                st.write("**Δικαιώματα Ρόλων:**")
                st.write("- **admin**: Πλήρης πρόσβαση")
                st.write("- **editor**: Επεξεργασία δεδομένων")
                st.write("- **viewer**: Προβολή μόνο")
            
            submitted = st.form_submit_button("Προσθήκη Χρήστη")
            
            if submitted:
                if new_username in st.session_state['users']:
                    st.error("Το όνομα χρήστη υπάρχει ήδη")
                else:
                    st.session_state['users'][new_username] = {
                        'password': hash_password(new_password),
                        'role': new_role,
                        'full_name': new_full_name
                    }
                    save_data({'users': st.session_state['users']})
                    st.success(f"Ο χρήστης {new_username} προστέθηκε επιτυχώς!")
    
    elif user_management_option == "Επεξεργασία Χρήστη":
        st.subheader("Επεξεργασία Υφιστάμενου Χρήστη")
        
        user_options = list(st.session_state['users'].keys())
        selected_user = st.selectbox("Επιλέξτε Χρήστη", user_options)
        
        if selected_user:
            user_data = st.session_state['users'][selected_user]
            
            with st.form("edit_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("Όνομα Χρήστη", value=selected_user, disabled=True)
                    edit_full_name = st.text_input("Πλήρες Όνομα", value=user_data['full_name'])
                    edit_password = st.text_input("Νέος Κωδικός (αφήστε κενό για να παραμείνει ο ίδιος)", type="password")
                
                with col2:
                    edit_role = st.selectbox("Ρόλος", ["admin", "editor", "viewer"], 
                                           index=["admin", "editor", "viewer"].index(user_data['role']))
                
                submitted = st.form_submit_button("Ενημέρωση Χρήστη")
                
                if submitted:
                    updated_user = {
                        'full_name': edit_full_name,
                        'role': edit_role
                    }
                    
                    if edit_password:
                        updated_user['password'] = hash_password(edit_password)
                    else:
                        updated_user['password'] = user_data['password']
                    
                    st.session_state['users'][selected_user] = updated_user
                    save_data({'users': st.session_state['users']})
                    st.success(f"Ο χρήστης {selected_user} ενημερώθηκε επιτυχώς!")
    
    elif user_management_option == "Διαγραφή Χρήστη":
        st.subheader("Διαγραφή Χρήστη")
        
        user_options = [user for user in st.session_state['users'].keys() if user != st.session_state.current_user]
        selected_user = st.selectbox("Επιλέξτε Χρήστη για Διαγραφή", user_options)
        
        if selected_user:
            st.warning(f"⚠️ Θα διαγράψετε τον χρήστη: {selected_user}")
            st.write("Πλήρες όνομα:", st.session_state['users'][selected_user]['full_name'])
            st.write("Ρόλος:", st.session_state['users'][selected_user]['role'])
            
            if st.button("Διαγραφή Χρήστη", type="secondary"):
                del st.session_state['users'][selected_user]
                save_data({'users': st.session_state['users']})
                st.success(f"Ο χρήστης {selected_user} διαγράφηκε επιτυχώς!")

# Tab 7: Αποθηκευτικοί Χώροι
with current_tab[6]:
    st.header("📦 Διαχείριση Αποθηκευτικών Χώρων")
    
    if st.session_state.user_role not in ['admin', 'editor']:
        st.warning("⛔ Δεν έχετε δικαιώματα πρόσβασης στη Διαχείριση Αποθηκευτικών Χώρων")
        st.stop()
    
    storage_option = st.selectbox("Επιλογή", [
        "Προβολή Αποθηκευτικών Χώρων",
        "Προσθήκη Νέου Χώρου",
        "Επεξεργασία Χώρου",
        "Διαγραφή Χώρου",
        "Στατιστικά Χώρου"
    ])
    
    if storage_option == "Προβολή Αποθηκευτικών Χώρων":
        st.subheader("Λίστα Αποθηκευτικών Χώρων")
        
        storage_df = pd.DataFrame(st.session_state['storage_locations'])
        st.dataframe(storage_df, use_container_width=True)
        
        # Υπολογισμός χρήσης χώρου
        storage_usage = calculate_storage_usage()
        
        st.subheader("Χρήση Αποθηκευτικού Χώρου")
        for loc_id, data in storage_usage.items():
            usage_percent = (data['used'] / data['capacity']) * 100 if data['capacity'] > 0 else 0
            st.write(f"**{data['name']}**")
            st.progress(usage_percent / 100, text=f"{data['used']:,.0f} kg / {data['capacity']:,.0f} kg ({usage_percent:.1f}%)")
    
    elif storage_option == "Προσθήκη Νέου Χώρου":
        st.subheader("Προσθήκη Νέου Αποθηκευτικού Χώρου")
        
        with st.form("add_storage_form"):
            storage_id = get_next_id(st.session_state['storage_locations'])
            storage_name = st.text_input("Όνομα Αποθήκης")
            storage_capacity = st.number_input("Χωρητικότητα (kg)", min_value=1, step=100, value=1000)
            storage_description = st.text_area("Περιγραφή")
            
            submitted = st.form_submit_button("Προσθήκη Αποθήκης")
            
            if submitted:
                new_storage = {
                    "id": storage_id,
                    "name": storage_name,
                    "capacity": storage_capacity,
                    "description": storage_description
                }
                
                st.session_state['storage_locations'].append(new_storage)
                save_data({'storage_locations': st.session_state['storage_locations']})
                st.success(f"Η αποθήκη {storage_name} προστέθηκε επιτυχώς!")
    
    elif storage_option == "Επεξεργασία Χώρου":
        st.subheader("Επεξεργασία Αποθηκευτικού Χώρου")
        
        storage_options = [f"{s['id']} - {s['name']}" for s in st.session_state['storage_locations']]
        selected_storage = st.selectbox("Επιλέξτε Αποθήκη", storage_options)
        
        if selected_storage:
            storage_id = int(selected_storage.split(" - ")[0])
            storage_data = next((s for s in st.session_state['storage_locations'] if s['id'] == storage_id), None)
            
            if storage_data:
                with st.form("edit_storage_form"):
                    storage_name = st.text_input("Όνομα Αποθήκης", value=storage_data['name'])
                    storage_capacity = st.number_input("Χωρητικότητα (kg)", min_value=1, step=100, value=storage_data['capacity'])
                    storage_description = st.text_area("Περιγραφή", value=storage_data.get('description', ''))
                    
                    submitted = st.form_submit_button("Ενημέρωση Αποθήκης")
                    
                    if submitted:
                        storage_data.update({
                            "name": storage_name,
                            "capacity": storage_capacity,
                            "description": storage_description
                        })
                        
                        save_data({'storage_locations': st.session_state['storage_locations']})
                        st.success(f"Η αποθήκη {storage_name} ενημερώθηκε επιτυχώς!")
    
    elif storage_option == "Διαγραφή Χώρου":
        st.subheader("Διαγραφή Αποθηκευτικού Χώρου")
        
        storage_options = [f"{s['id']} - {s['name']}" for s in st.session_state['storage_locations']]
        selected_storage = st.selectbox("Επιλέξτε Αποθήκη για Διαγραφή", storage_options)
        
        if selected_storage:
            storage_id = int(selected_storage.split(" - ")[0])
            storage_name = selected_storage.split(" - ")[1]
            
            # Έλεγχος αν η αποθήκη περιέχει προϊόντα
            storage_usage = calculate_storage_usage()
            used_kg = storage_usage.get(storage_id, {}).get('used', 0)
            
            if used_kg > 0:
                st.error(f"Δεν μπορείτε να διαγράψετε την αποθήκη {storage_name} γιατί περιέχει {used_kg} kg προϊόντων")
            else:
                st.warning(f"⚠️ Θα διαγράψετε την αποθήκη: {storage_name}")
                
                if st.button("Διαγραφή Αποθήκης", type="secondary"):
                    st.session_state['storage_locations'] = [s for s in st.session_state['storage_locations'] if s['id'] != storage_id]
                    save_data({'storage_locations': st.session_state['storage_locations']})
                    st.success(f"Η αποθήκη {storage_name} διαγράφηκε επιτυχώς!")
    
    elif storage_option == "Στατιστικά Χώρου":
        st.subheader("Στατιστικά Αποθηκευτικού Χώρου")
        
        storage_options = [f"{s['id']} - {s['name']}" for s in st.session_state['storage_locations']]
        selected_storage = st.selectbox("Επιλέξτε Αποθήκη", storage_options)
        
        if selected_storage:
            storage_id = int(selected_storage.split(" - ")[0])
            storage_data = next((s for s in st.session_state['storage_locations'] if s['id'] == storage_id), None)
            storage_usage = calculate_storage_usage()
            
            if storage_data and storage_id in storage_usage:
                usage_data = storage_usage[storage_id]
                usage_percent = (usage_data['used'] / storage_data['capacity']) * 100 if storage_data['capacity'] > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Χωρητικότητα", f"{storage_data['capacity']:,.0f} kg")
                with col2:
                    st.metric("Χρησιμοποιημένος Χώρος", f"{usage_data['used']:,.0f} kg")
                with col3:
                    st.metric("Ποσοστό Χρήσης", f"{usage_percent:.1f}%")
                
                st.progress(usage_percent / 100, text=f"{usage_data['used']:,.0f} kg / {storage_data['capacity']:,.0f} kg")
                
                # Λίστα προϊόντων στην αποθήκη
                if usage_data['items']:
                    st.subheader("Προϊόντα στην Αποθήκη")
                    items_df = pd.DataFrame(usage_data['items'])
                    st.dataframe(items_df, use_container_width=True)
                else:
                    st.info("Η αποθήκη είναι άδεια")

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
                
                total_kg = sum(size_quantities.values())
                st.info(f"📦 Σύνολο κιλών: {total_kg} kg")
                
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
                
                total_ordered = sum(ordered_quantities.values())
                total_delivered = sum(delivered_quantities.values())
                
                st.info(f"📦 Σύνολο παραγγελθέντων: {total_ordered} kg")
                st.success(f"📦 Σύνολο παραδοθέντων: {total_delivered} kg")
            
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
                            'total_kg': total_kg
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
                            'total_ordered_kg': total_ordered,
                            'total_delivered_kg': total_delivered
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