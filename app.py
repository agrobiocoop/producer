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

# Στήλες για το tab layout
tabs = ["Κεντρική Βάση", "Νέα Παραλαβή", "Νέα Παραγγελία", "Αναφορές", "Διαχείριση", "Επεξεργασία"]
if st.session_state.user_role == 'admin':
    tabs.append("Διαχείριση Χρηστών")

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
            
            order_options = ["Καμία"] + [f"{o['id']} - {o.get('customer', '')}" for o in st.session_state['orders']]
            related_order = st.selectbox("Σχετίζεται με Παραγγελία", options=order_options)
            order_id = None if related_order == "Καμία" else int(related_order.split(" - ")[0])
            
            variety = st.text_input("Ποικιλία")
            lot = st.text_input("Λοτ")
            storage = st.text_input("Αποθηκευτικός Χώρος")
            responsible = st.text_input("Υπεύθυνος")
        
        with col2:
            st.subheader("📊 Ποσότητες ανά Νούμερο")
            sizes = ["10", "12", "14", "16", "18", "20", "22", "24", "26", "26-32", "Διάφορα"]
            size_quantities = {}
            for size in sizes:
                size_quantities[size] = st.number_input(f"Ποσότητα για νούμερο {size}", min_value=0, step=1, key=f"size_{size}")
            
            st.subheader("🏆 Ποσότητες ανά Ποιότητα")
            qualities = ["Ι", "ΙΙ", "ΙΙΙ", "Σκάρτα", "Προς Μεταποίηση"]
            quality_quantities = {}
            for quality in qualities:
                quality_quantities[quality] = st.number_input(f"Ποσότητα για {quality}", min_value=0, step=1, key=f"qual_{quality}")
            
            certifications = st.multiselect(
                "📑 Πιστοποιήσεις",
                ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ", "Συνδυασμός"]
            )
            
            agreed_price = st.number_input("💰 Συμφωνηθείσα Τιμή", min_value=0.0, step=0.01)
            payment_method = st.selectbox("💳 Πληρωμή", ["Μετρητά", "Τραπεζική ΚατάΘεση", "Πιστωτική Κάρτα"])
            observations = st.text_area("📝 Παρατηρήσεις")
        
        submitted = st.form_submit_button("✅ Καταχώρηση Παραλαβής")
        
        if submitted:
            new_receipt = {
                "id": receipt_id,
                "receipt_date": receipt_date.strftime("%Y-%m-%d"),
                "packaging_date": packaging_date.strftime("%Y-%m-%d") if packaging_date else "",
                "producer_id": producer_id,
                "order_id": order_id,
                "variety": variety,
                "lot": lot,
                "storage": storage,
                "responsible": responsible,
                "size_quantities": size_quantities,
                "quality_quantities": quality_quantities,
                "certifications": certifications,
                "agreed_price": agreed_price,
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

# Tab 3: Νέα Παραγγελία (παρόμοια με παραλαβή)

# Tab 4: Αναφορές
with current_tab[3]:
    st.header("📈 Αναφορές και Εκτυπώσεις")
    
    report_type = st.selectbox("Επιλέξτε τύπο αναφοράς", [
        "Αναφορά Παραλαβών", 
        "Αναφορά Παραγγελιών",
        "Αναφορά Παραγωγών",
        "Αναφορά Πελατών"
    ])
    
    if report_type == "Αναφορά Παραλαβών":
        if st.session_state['receipts']:
            receipts_df = pd.DataFrame(st.session_state['receipts'])
            
            # Φίλτρα
            col1, col2 = st.columns(2)
            with col1:
                date_from = st.date_input("Από ημερομηνία")
            with col2:
                date_to = st.date_input("Έως ημερομηνία")
            
            filtered_df = receipts_df.copy()
            if date_from:
                filtered_df = filtered_df[filtered_df['receipt_date'] >= date_from.strftime("%Y-%m-%d")]
            if date_to:
                filtered_df = filtered_df[filtered_df['receipt_date'] <= date_to.strftime("%Y-%m-%d")]
            
            st.dataframe(filtered_df, use_container_width=True)
            
            # Κουμπιά εξαγωγής
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📄 Εξαγωγή σε CSV"):
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Κατεβάστε CSV",
                        data=csv,
                        file_name="παραλαβές.csv",
                        mime="text/csv"
                    )
            with col2:
                if st.button("📊 Εξαγωγή σε Excel"):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        filtered_df.to_excel(writer, sheet_name='Παραλαβές', index=False)
                    st.download_button(
                        label="⬇️ Κατεβάστε Excel",
                        data=output.getvalue(),
                        file_name="παραλαβές.xlsx",
                        mime="application/vnd.ms-excel"
                    )
            with col3:
                if st.button("🖨️ Εκτύπωση Αναφοράς"):
                    st.success("Η αναφορά είναι έτοιμη για εκτύπωση. Πατήστε Ctrl+P")
        else:
            st.info("Δεν υπάρχουν καταχωρημένες παραλαβές")

# Tab 5: Διαχείριση
with current_tab[4]:
    if can_edit():
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
        
        with st.form(f"{entity_key}_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                entity_id = st.number_input("ID", min_value=1, step=1, value=get_next_id(entities))
                name = st.text_input("Όνομα")
            
            with col2:
                if entity_type == "Παραγωγοί":
                    quantity = st.number_input("Ποσότητα", min_value=0, step=1)
                    certifications = st.multiselect(
                        "Πιστοποιήσεις",
                        ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
                    )
                elif entity_type == "Πελάτες":
                    address = st.text_input("Διεύθυνση")
                    phone = st.text_input("Τηλέφωνο")
                else:
                    contact = st.text_input("Πρόσωπο Επικοινωνίας")
                    phone = st.text_input("Τηλέφωνο")
            
            submitted = st.form_submit_button("💾 Αποθήκευση")
            
            if submitted:
                # ... κώδικας για αποθήκευση ...
                pass
        
        st.subheader(f"Κατάλογος {entity_type}")
        if entities:
            df = pd.DataFrame(entities)
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"Δεν υπάρχουν καταχωρημένοι {entity_type}")
    else:
        st.warning("⛔ Δεν έχετε δικαιώματα διαχείρισης")

# Tab 6: Επεξεργασία
with current_tab[5]:
    st.header("✏️ Επεξεργασία Δεδομένων")
    
    data_type = st.selectbox("Επιλέξτε τύπο δεδομένων", ["Παραλαβές", "Παραγγελίες"])
    
    if data_type == "Παραλαβές":
        items = st.session_state['receipts']
        item_key = 'receipts'
    else:
        items = st.session_state['orders']
        item_key = 'orders'
    
    if items:
        options = [f"{item['id']} - {item.get('variety', '')}" for item in items]
        selected_option = st.selectbox("Επιλέξτε εγγραφή", options)
        
        if selected_option:
            selected_id = int(selected_option.split(" - ")[0])
            selected_item = next((item for item in items if item['id'] == selected_id), None)
            
            if selected_item:
                st.json(selected_item)
                
                if can_delete():
                    if st.button("🗑️ Διαγραφή", type="secondary"):
                        st.session_state[item_key] = [item for item in items if item['id'] != selected_id]
                        save_data({item_key: st.session_state[item_key]})
                        st.success("✅ Διαγραφή επιτυχής!")
                        time.sleep(2)
                        st.rerun()
    else:
        st.info("Δεν υπάρχουν διαθέσιμες εγγραφές")

# Tab 7: Διαχείριση Χρηστών (μόνο για admin)
if st.session_state.user_role == 'admin' and len(current_tab) > 6:
    with current_tab[6]:
        st.header("👥 Διαχείριση Χρηστών")
        
        st.subheader("Νέος Χρήστης")
        with st.form("user_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_username = st.text_input("Όνομα χρήστη")
                new_password = st.text_input("Κωδικός πρόσβασης", type="password")
            
            with col2:
                new_fullname = st.text_input("Πλήρες όνομα")
                confirm_password = st.text_input("Επιβεβαίωση κωδικού", type="password")
            
            with col3:
                new_role = st.selectbox("Ρόλος", ["viewer", "editor", "admin"])
            
            submitted = st.form_submit_button("➕ Προσθήκη Χρήστη")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Οι κωδικοί δεν ταιριάζουν")
                elif new_username in st.session_state['users']:
                    st.error("Ο χρήστης υπάρχει ήδη")
                else:
                    st.session_state['users'][new_username] = {
                        'password': hash_password(new_password),
                        'role': new_role,
                        'full_name': new_fullname
                    }
                    save_data({'users': st.session_state['users']})
                    st.success(f"✅ Ο χρήστης {new_username} προστέθηκε!")
        
        st.subheader("Υπάρχοντες Χρήστες")
        users_df = pd.DataFrame([
            {'username': user, 'role': data['role'], 'full_name': data['full_name']}
            for user, data in st.session_state['users'].items()
        ])
        st.dataframe(users_df, use_container_width=True)

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