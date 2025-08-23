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

def init_admin_user():
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

# Συναρτήσεις αυτόματης αποθήκευσης και φόρτωσης
def load_data():
    """Φόρτωση δεδομένων από αρχεία"""
    data_files = {
        'users': 'users.json',
        'producers': 'producers.json',
        'customers': 'customers.json', 
        'agencies': 'agencies.json',
        'receipts': 'receipts.json',
        'orders': 'orders.json'
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
init_admin_user()
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

def delete_item(item_type, item_id):
    """Διαγραφή αντικειμένου"""
    st.session_state[item_type] = [item for item in st.session_state[item_type] if item['id'] != item_id]
    save_data({item_type: st.session_state[item_type]})
    st.success("Διαγραφή επιτυχής!")
    time.sleep(1)
    st.rerun()

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
tabs = ["Κεντρική Βάση", "Νέα Παραλαβή", "Νέα Παραγγελία", "Αναφορές", "Διαχείριση", "Διαχείριση Χρηστών"]
current_tab = st.tabs(tabs)

# Tab 1: Κεντρική Βάση
with current_tab[0]:
    st.header("📊 Κεντρική Βάση Δεδομένων")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👨‍🌾 Παραγωγοί")
        producers_df = pd.DataFrame(st.session_state['producers'])
        if not producers_df.empty:
            st.dataframe(producers_df, use_container_width=True)
        else:
            st.info("Δεν υπάρχουν καταχωρημένοι παραγωγοί")
    
    with col2:
        st.subheader("👥 Πελάτες")
        customers_df = pd.DataFrame(st.session_state['customers'])
        if not customers_df.empty:
            st.dataframe(customers_df, use_container_width=True)
        else:
            st.info("Δεν υπάρχουν καταχωρημένοι πελάτες")
    
    st.subheader("📦 Παραλαβές")
    if st.session_state['receipts']:
        receipts_df = pd.DataFrame(st.session_state['receipts'])
        st.dataframe(receipts_df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν καταχωρημένες παραλαβές")
    
    st.subheader("📋 Παραγγελίες")
    if st.session_state['orders']:
        orders_df = pd.DataFrame(st.session_state['orders'])
        st.dataframe(orders_df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν καταχωρημένες παραγγελίες")

# Tab 2: Νέα Παραλαβή
with current_tab[1]:
    st.header("📥 Καταχώρηση Νέας Παραλαβής")
    
    with st.form("receipt_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            receipt_id = st.number_input("Αριθμός Παραλαβής", min_value=1, step=1, value=get_next_id(st.session_state['receipts']))
            
            # Επιλογή ημερομηνίας
            date_option = st.radio("Ημερομηνία Παραλαβής:", ["Σήμερα", "Επιλογή Ημερομηνίας"])
            if date_option == "Σήμερα":
                receipt_date = datetime.today()
            else:
                receipt_date = st.date_input("Επιλέξτε Ημερομηνία Παραλαβής")
            
            # Επιλογή παραγωγού
            producer_options = [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
            selected_producer = st.selectbox("Παραγωγός", options=producer_options)
            producer_id = int(selected_producer.split(" - ")[0]) if selected_producer else None
            
            variety = st.text_input("Ποικιλία")
            lot = st.text_input("Λοτ")
        
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
                ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ", "Συνδυασμός"]
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
                "producer_name": selected_producer.split(" - ")[1] if selected_producer else "",
                "variety": variety,
                "lot": lot,
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
            
            # Επιλογή ημερομηνίας
            date_option = st.radio("Ημερομηνία Παραγγελίας:", ["Σήμερα", "Επιλογή Ημερομηνίας"])
            if date_option == "Σήμερα":
                order_date = datetime.today()
            else:
                order_date = st.date_input("Επιλέξτε Ημερομηνία Παραγγελίας")
            
            # Επιλογή πελάτη
            customer_options = [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
            selected_customer = st.selectbox("Πελάτης", options=customer_options)
            customer_id = int(selected_customer.split(" - ")[0]) if selected_customer else None
            customer_name = selected_customer.split(" - ")[1] if selected_customer else ""
            
            variety = st.text_input("Ποικιλία Παραγγελίας")
            lot = st.text_input("Λοτ Παραγγελίας")
        
        with col2:
            # Ποσότητες παραγγελίας
            st.subheader("📦 Ποσότητες Παραγγελίας")
            sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
            order_quantities = {}
            for size in sizes:
                order_quantities[size] = st.number_input(f"Ποσότητα για νούμερο {size}", min_value=0, step=1, key=f"order_size_{size}")
            
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
                "lot": lot,
                "quantities": order_quantities,
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
    
    st.subheader("Αναφορές Παραλαβών")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Φίλτρα ημερομηνιών
        st.write("**Φίλτρα Αναφοράς**")
        start_date = st.date_input("Από ημερομηνία", value=datetime.today() - timedelta(days=30))
        end_date = st.date_input("Έως ημερομηνία", value=datetime.today())
        
        # Φίλτρα παραγωγών
        producer_options = ["Όλοι"] + [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
        selected_producer = st.selectbox("Παραγωγός", options=producer_options)
        
        # Φίλτρα πιστοποιήσεων
        cert_options = ["Όλες"] + ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
        selected_cert = st.selectbox("Πιστοποίηση", options=cert_options)
    
    with col2:
        # Δεδομένα αναφοράς
        filtered_receipts = []
        for receipt in st.session_state['receipts']:
            receipt_date = datetime.strptime(receipt['receipt_date'], '%Y-%m-%d').date()
            
            # Φιλτράρισμα ημερομηνιών
            if receipt_date < start_date or receipt_date > end_date:
                continue
            
            # Φιλτράρισμα παραγωγού
            if selected_producer != "Όλοι":
                producer_id = int(selected_producer.split(" - ")[0])
                if receipt.get('producer_id') != producer_id:
                    continue
            
            # Φιλτράρισμα πιστοποιήσεων
            if selected_cert != "Όλες":
                if selected_cert not in receipt.get('certifications', []):
                    continue
            
            filtered_receipts.append(receipt)
        
        # Στατιστικά
        total_kg = sum(r['total_kg'] for r in filtered_receipts)
        total_value = sum(r['total_value'] for r in filtered_receipts)
        total_receipts = len(filtered_receipts)
        
        st.metric("Συνολικές Παραλαβές", total_receipts)
        st.metric("Συνολικά Κιλά", f"{total_kg} kg")
        st.metric("Συνολική Αξία", f"{total_value:.2f} €")
    
    # Πίνακας δεδομένων
    if filtered_receipts:
        df = pd.DataFrame(filtered_receipts)
        st.dataframe(df[['id', 'receipt_date', 'producer_name', 'total_kg', 'total_value', 'certifications']], use_container_width=True)
        
        # Εξαγωγή δεδομένων
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Εξαγωγή σε CSV",
            data=csv,
            file_name=f"αναφορά_παραλαβών_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.info("Δεν βρέθηκαν δεδομένα για τα επιλεγμένα φίλτρα")
    
    st.subheader("Αναφορές Πωλήσεων (Παραγγελιών)")
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Φίλτρα ημερομηνιών για πωλήσεις
        st.write("**Φίλτρα Πωλήσεων**")
        start_date_sales = st.date_input("Από ημερομηνία Πωλήσεων", value=datetime.today() - timedelta(days=30), key="sales_start")
        end_date_sales = st.date_input("Έως ημερομηνία Πωλήσεων", value=datetime.today(), key="sales_end")
    
    with col4:
        # Δεδομένα πωλήσεων
        filtered_orders = []
        for order in st.session_state['orders']:
            order_date = datetime.strptime(order['date'], '%Y-%m-%d').date()
            
            if order_date < start_date_sales or order_date > end_date_sales:
                continue
            
            filtered_orders.append(order)
        
        # Στατιστικά πωλήσεων
        total_kg_sales = sum(o['total_kg'] for o in filtered_orders)
        total_value_sales = sum(o['total_value'] for o in filtered_orders)
        total_orders = len(filtered_orders)
        
        st.metric("Συνολικές Παραγγελίες", total_orders)
        st.metric("Συνολικά Κιλά Πωλήσεων", f"{total_kg_sales} kg")
        st.metric("Συνολική Αξία Πωλήσεων", f"{total_value_sales:.2f} €")
    
    # Πίνακας πωλήσεων
    if filtered_orders:
        df_orders = pd.DataFrame(filtered_orders)
        st.dataframe(df_orders[['id', 'date', 'customer', 'total_kg', 'total_value']], use_container_width=True)
        
        # Εξαγωγή πωλήσεων
        csv_orders = df_orders.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Εξαγωγή Πωλήσεων CSV",
            data=csv_orders,
            file_name=f"αναφορά_πωλήσεων_{start_date_sales}_{end_date_sales}.csv",
            mime="text/csv"
        )

# Tab 5: Διαχείριση
with current_tab[4]:
    st.header("⚙️ Διαχείριση Οντοτήτων")
    
    entity_type = st.selectbox("Επιλέξτε τύπο οντότητας", ["Παραγωγοί", "Πελάτες"])
    
    if entity_type == "Παραγωγοί":
        entities = st.session_state['producers']
        entity_key = 'producers'
    else:
        entities = st.session_state['customers']
        entity_key = 'customers'
    
    st.subheader(f"Διαχείριση {entity_type}")
    
    # Φόρμα προσθήκης νέου
    with st.form(f"{entity_key}_form"):
        entity_id = st.number_input("ID", min_value=1, step=1, value=get_next_id(entities))
        name = st.text_input("Όνομα")
        
        if entity_type == "Παραγωγοί":
            quantity = st.number_input("Ποσότητα", min_value=0, step=1)
            certifications_options = ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
            certifications = st.multiselect("Πιστοποιήσεις", certifications_options)
        else:
            address = st.text_input("Διεύθυνση")
            phone = st.text_input("Τηλέφωνο")
        
        submitted = st.form_submit_button("💾 Προσθήκη")
        
        if submitted:
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
            time.sleep(1)
            st.rerun()
    
    # Κατάλογος οντοτήτων με δυνατότητα διαγραφής
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
                    st.success("✅ Διαγραφή επιτυχής!")
                    time.sleep(1)
                    st.rerun()
    else:
        st.info(f"Δεν υπάρχουν καταχωρημένοι {entity_type}")

# Tab 6: Διαχείριση Χρηστών
with current_tab[5]:
    if st.session_state.user_role == 'admin':
        st.header("👥 Διαχείριση Χρηστών")
        
        st.subheader("Υπάρχοντες Χρήστες")
        users_df = pd.DataFrame([
            {'username': user, 'role': data['role'], 'full_name': data.get('full_name', '')}
            for user, data in st.session_state['users'].items()
        ])
        st.dataframe(users_df, use_container_width=True)
        
        st.subheader("Δημιουργία Νέου Χρήστη")
        with st.form("new_user_form"):
            new_username = st.text_input("Νέο Όνομα Χρήστη")
            new_password = st.text_input("Νέος Κωδικός", type="password")
            confirm_password = st.text_input("Επιβεβαίωση Κωδικού", type="password")
            new_role = st.selectbox("Ρόλος", ["viewer", "editor", "admin"])
            new_fullname = st.text_input("Πλήρες Όνομα")
            
            if st.form_submit_button("➕ Δημιουργία Χρήστη"):
                if new_password == confirm_password:
                    if new_username not in st.session_state['users']:
                        st.session_state['users'][new_username] = {
                            'password': hash_password(new_password),
                            'role': new_role,
                            'full_name': new_fullname
                        }
                        save_data({'users': st.session_state['users']})
                        st.success(f"✅ Ο χρήστης {new_username} δημιουργήθηκε!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Το όνομα χρήστη υπάρχει ήδη")
                else:
                    st.error("❌ Οι κωδικοί δεν ταιριάζουν")
        
        st.subheader("Διαχείριση Υφιστάμενων Χρηστών")
        user_options = list(st.session_state['users'].keys())
        selected_user = st.selectbox("Επιλέξτε χρήστη για διαχείριση", user_options)
        
        if selected_user:
            user_data = st.session_state['users'][selected_user]
            
            col1, col2 = st.columns(2)
            
            with col1:
                with st.form("change_password_form"):
                    st.write(f"**Αλλαγή Κωδικού για: {selected_user}**")
                    new_password = st.text_input("Νέος Κωδικός", type="password", key="new_pass")
                    confirm_password = st.text_input("Επιβεβαίωση Κωδικού", type="password", key="confirm_pass")
                    
                    if st.form_submit_button("🔒 Αλλαγή Κωδικού"):
                        if new_password == confirm_password:
                            st.session_state['users'][selected_user]['password'] = hash_password(new_password)
                            save_data({'users': st.session_state['users']})
                            st.success(f"✅ Ο κωδικός για τον χρήστη {selected_user} άλλαξε επιτυχώς!")
                        else:
                            st.error("❌ Οι κωδικοί δεν ταιριάζουν")
            
            with col2:
                with st.form("change_role_form"):
                    st.write(f"**Αλλαγή Ρόλου για: {selected_user}**")
                    new_role = st.selectbox("Νέος Ρόλος", ["viewer", "editor", "admin"], 
                                          index=["viewer", "editor", "admin"].index(user_data['role']))
                    
                    if st.form_submit_button("🎭 Αλλαγή Ρόλου"):
                        st.session_state['users'][selected_user]['role'] = new_role
                        save_data({'users': st.session_state['users']})
                        st.success(f"✅ Ο ρόλος για τον χρήστη {selected_user} άλλαξε επιτυχώς!")
                
                if selected_user != 'admin' and st.button("🗑️ Διαγραφή Χρήστη", key=f"del_user_{selected_user}"):
                    del st.session_state['users'][selected_user]
                    save_data({'users': st.session_state['users']})
                    st.success(f"✅ Ο χρήστης {selected_user} διαγράφηκε!")
                    time.sleep(1)
                    st.rerun()
    else:
        st.warning("⛔ Δεν έχετε δικαιώματα διαχείρισης χρηστών")

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
    
    st.sidebar.download_button(
        label="💾 Κατεβάστε Όλα",
        data=output.getvalue(),
        file_name="ολοκληρωμένη_βάση.xlsx",
        mime="application/vnd.ms-excel"
    )

if st.sidebar.button("🔄 Ανανέωση Δεδομένων"):
    data = load_data()
    for key, value in data.items():
        st.session_state[key] = value
    st.sidebar.success("✅ Τα δεδομένα ανανεώθηκαν!")