import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
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

# Σύνδεση χρήστη
if not st.session_state.authenticated:
    login()
    st.stop()

# Κύρια εφαρμογή
st.sidebar.title(f"👋 Καλώς ήρθατε, {st.session_state.current_user}")
st.sidebar.write(f"**Ρόλος:** {st.session_state.user_role}")

if st.sidebar.button("🚪 Αποσύνδεση"):
    logout()

# Προσθήκη δειγματικών δεδομένων αν χρειάζεται
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

if not st.session_state['agencies']:
    st.session_state['agencies'] = [
        {"id": 1, "name": "Πρακτορείο Α", "contact": "Πρόσωπο Α", "phone": "2103333333"},
        {"id": 2, "name": "Πρακτορείο Β", "contact": "Πρόσωπο Β", "phone": "2104444444"}
    ]
    save_data({'agencies': st.session_state['agencies']})

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
            receipt_date = st.date_input("Ημερομηνία Παραλαβής", value=datetime.today())
            packaging_date = st.date_input("Ημερομηνία Συσκευασίας", value=datetime.today())
            
            producer_options = [f"{p['id']} - {p['name']}" for p in st.session_state['producers']]
            selected_producer = st.selectbox("Παραγωγός", options=producer_options)
            producer_id = int(selected_producer.split(" - ")[0]) if selected_producer else None
            
            # ΝΕΟ: DROPDOWN ΠΕΛΑΤΕΣ - ΑΠΕΣΤΑΛΗΣΑΝ
            customer_options = ["Κανένας"] + [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
            shipped_to = st.selectbox("Απεστάλησαν", options=customer_options)
            shipped_to_id = None if shipped_to == "Κανένας" else int(shipped_to.split(" - ")[0])
            
            variety = st.text_input("Ποικιλία")
            lot = st.text_input("Λοτ")
            storage = st.text_input("Αποθηκευτικός Χώρος")
            responsible = st.text_input("Υπεύθυνος")
        
        with col2:
            # Ποσότητες ανά νούμερο
            st.subheader("📊 Ποσότητες ανά Νούμερο")
            sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
            size_quantities = {}
            for size in sizes:
                size_quantities[size] = st.number_input(f"Ποσότητα για νούμερο {size}", min_value=0, step=1, key=f"size_{size}")
            
            # Ποσότητες ανά ποιότητα
            st.subheader("🏆 Ποσότητες ανά Ποιότητα")
            qualities = ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Προς Μεταποίηση"]
            quality_quantities = {}
            for quality in qualities:
                quality_quantities[quality] = st.number_input(f"Ποσότητα για {quality}", min_value=0, step=1, key=f"qual_{quality}")
            
            # Πιστοποιήσεις
            certifications = st.multiselect(
                "📑 Πιστοποιήσεις",
                ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ", "Συνδυασμός"]
            )
            
            # ΣΥΜΦΩΝΗΘΕΙΣΑ ΤΙΜΗ
            agreed_price_per_kg = st.number_input("💰 Συμφωνηθείσα Τιμή ανά κιλό", min_value=0.0, step=0.01, value=0.0, help="Τιμή ανά κιλό σε €")
            
            # Υπολογισμός συνολικής αξίας
            total_kg = sum(size_quantities.values())
            total_value = total_kg * agreed_price_per_kg if agreed_price_per_kg else 0
            
            if total_kg > 0:
                st.info(f"📦 Σύνολο κιλών: {total_kg} kg")
                st.success(f"💶 Συνολική αξία: {total_value:.2f} €")
            
            payment_method = st.selectbox("💳 Πληρωμή", ["Μετρητά", "Τραπεζική ΚατάΘεση", "Πιστωτική Κάρτα"])
            observations = st.text_area("📝 Παρατηρήσεις")
        
        submitted = st.form_submit_button("✅ Καταχώρηση Παραλαβής")
        
        if submitted:
            new_receipt = {
                "id": receipt_id,
                "receipt_date": receipt_date.strftime("%Y-%m-%d"),
                "packaging_date": packaging_date.strftime("%Y-%m-%d") if packaging_date else "",
                "producer_id": producer_id,
                "shipped_to_id": shipped_to_id,
                "shipped_to": shipped_to if shipped_to != "Κανένας" else None,
                "variety": variety,
                "lot": lot,
                "storage": storage,
                "responsible": responsible,
                "size_quantities": size_quantities,
                "quality_quantities": quality_quantities,
                "certifications": certifications,
                "agreed_price_per_kg": agreed_price_per_kg,
                "total_kg": total_kg,
                "total_value": total_value,
                "payment_method": payment_method,
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
            loading_date = st.date_input("Ημερομηνία Φόρτωσης", value=datetime.today())
            
            # Επιλογή πελάτη
            customer_options = [f"{c['id']} - {c['name']}" for c in st.session_state['customers']]
            selected_customer = st.selectbox("Πελάτης", options=customer_options)
            customer_id = int(selected_customer.split(" - ")[0]) if selected_customer else None
            customer_name = selected_customer.split(" - ")[1] if selected_customer else ""
            
            # Επιλογή πρακτορείου
            agency_options = [f"{a['id']} - {a['name']}" for a in st.session_state['agencies']]
            selected_agency = st.selectbox("Πρακτορείο", options=agency_options)
            agency_id = int(selected_agency.split(" - ")[0]) if selected_agency else None
            
            variety = st.text_input("Ποικιλία Παραγγελίας")
            lot = st.text_input("Λοτ Παραγγελίας")
        
        with col2:
            # Ποσότητες παραγγελίας
            st.subheader("📦 Ποσότητες Παραγγελίας")
            sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
            order_quantities = {}
            for size in sizes:
                order_quantities[size] = st.number_input(f"Ποσότητα για νούμερο {size}", min_value=0, step=1, key=f"order_size_{size}")
            
            # ΣΥΜΦΩΝΗΘΕΙΣΑ ΤΙΜΗ
            agreed_price_per_kg = st.number_input("💰 Συμφωνηθείσα Τιμή ανά κιλό", min_value=0.0, step=0.01, value=0.0, help="Τιμή ανά κιλό σε €")
            
            # Υπολογισμός συνολικής αξίας
            total_kg = sum(order_quantities.values())
            total_value = total_kg * agreed_price_per_kg if agreed_price_per_kg else 0
            
            if total_kg > 0:
                st.info(f"📦 Σύνολο κιλών: {total_kg} kg")
                st.success(f"💶 Συνολική αξία: {total_value:.2f} €")
            
            # Πληροφορίες πληρωμής
            payment_terms = st.text_area("💳 Όροι Πληρωμής")
            delivery_terms = st.text_area("🚚 Όροι Παράδοσης")
            order_observations = st.text_area("📝 Παρατηρήσεις Παραγγελίας")
        
        submitted = st.form_submit_button("✅ Καταχώρηση Παραγγελίας")
        
        if submitted:
            new_order = {
                "id": order_id,
                "date": order_date.strftime("%Y-%m-%d"),
                "loading_date": loading_date.strftime("%Y-%m-%d") if loading_date else "",
                "customer_id": customer_id,
                "customer": customer_name,
                "agency_id": agency_id,
                "variety": variety,
                "lot": lot,
                "quantities": order_quantities,
                "agreed_price_per_kg": agreed_price_per_kg,
                "total_kg": total_kg,
                "total_value": total_value,
                "payment_terms": payment_terms,
                "delivery_terms": delivery_terms,
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
    st.header("📈 Αναφορές και Εκτυπώσεις")
    
    st.subheader("Αναλυτικές Αναφορές")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Αναφορά Παραλαβών**")
        if st.session_state['receipts']:
            receipts_df = pd.DataFrame(st.session_state['receipts'])
            st.dataframe(receipts_df, use_container_width=True)
            
            # Εξαγωγή σε CSV
            csv = receipts_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Εξαγωγή Παραλαβών CSV",
                data=csv,
                file_name="παραλαβές.csv",
                mime="text/csv"
            )
        else:
            st.info("Δεν υπάρχουν καταχωρημένες παραλαβές")
    
    with col2:
        st.write("**Αναφορά Παραγγελιών**")
        if st.session_state['orders']:
            orders_df = pd.DataFrame(st.session_state['orders'])
            st.dataframe(orders_df, use_container_width=True)
            
            # Εξαγωγή σε CSV
            csv = orders_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Εξαγωγή Παραγγελιών CSV",
                data=csv,
                file_name="παραγγελίες.csv",
                mime="text/csv"
            )
        else:
            st.info("Δεν υπάρχουν καταχωρημένες παραγγελίες")
    
    st.subheader("Στατιστικά")
    if st.session_state['receipts']:
        total_receipts = len(st.session_state['receipts'])
        total_quantity = sum(sum(r['size_quantities'].values()) for r in st.session_state['receipts'])
        
        col1, col2 = st.columns(2)
        col1.metric("Συνολικές Παραλαβές", total_receipts)
        col2.metric("Συνολική Ποσότητα", f"{total_quantity} kg")
    else:
        st.info("Δεν υπάρχουν στατιστικά για εμφάνιση")

# Tab 5: Διαχείριση
with current_tab[4]:
    st.header("⚙️ Διαχείριση Οντοτήτων")
    
    entity_type = st.selectbox("Επιλέξτε τύπο οντότητας", ["Παραγωγοί", "Πελάτες", "Πρακτορεία"])
    
    if entity_type == "Παραγωγοί":
        entities = st.session_state['producers']
        entity_key = 'producers'
    elif entity_type == "Πελάτες":
        entities = st.session_state['customers']
        entity_key = 'customers'
    else:
        entities = st.session_state['agencies']
        entity_key = 'agencies'
    
    st.subheader(f"Διαχείριση {entity_type}")
    
    # Φόρμα προσθήκης νέου
    with st.form(f"{entity_key}_form"):
        entity_id = st.number_input("ID", min_value=1, step=1, value=get_next_id(entities))
        name = st.text_input("Όνομα")
        
        if entity_type == "Παραγωγοί":
            quantity = st.number_input("Ποσότητα", min_value=0, step=1)
            certifications_options = ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
            certifications = st.multiselect("Πιστοποιήσεις", certifications_options)
        elif entity_type == "Πελάτες":
            address = st.text_input("Διεύθυνση")
            phone = st.text_input("Τηλέφωνο")
        else:
            contact = st.text_input("Πρόσωπο Επικοινωνίας")
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
            elif entity_type == "Πελάτες":
                new_entity = {
                    "id": entity_id,
                    "name": name,
                    "address": address,
                    "phone": phone
                }
            else:
                new_entity = {
                    "id": entity_id,
                    "name": name,
                    "contact": contact,
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
                elif entity_type == "Πελάτες":
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
            {'username': user, 'role': data['role'], 'full_name': data['full_name']}
            for user, data in st.session_state['users'].items()
        ])
        st.dataframe(users_df, use_container_width=True)
        
        st.subheader("Αλλαγή Κωδικού")
        user_options = list(st.session_state['users'].keys())
        selected_user = st.selectbox("Επιλέξτε χρήστη", user_options)
        
        if selected_user:
            with st.form("change_password_form"):
                new_password = st.text_input("Νέος Κωδικός", type="password")
                confirm_password = st.text_input("Επιβεβαίωση Κωδικού", type="password")
                
                if st.form_submit_button("🔒 Αλλαγή Κωδικού"):
                    if new_password == confirm_password:
                        st.session_state['users'][selected_user]['password'] = hash_password(new_password)
                        save_data({'users': st.session_state['users']})
                        st.success(f"✅ Ο κωδικός για τον χρήστη {selected_user} άλλαξε επιτυχώς!")
                    else:
                        st.error("❌ Οι κωδικοί δεν ταιριάζουν")
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
        if st.session_state['agencies']:
            pd.DataFrame(st.session_state['agencies']).to_excel(writer, sheet_name='Πρακτορεία', index=False)
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