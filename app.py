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

# Προσπάθεια εισαγωγής QR code (αν είναι διαθέσιμο)
QR_AVAILABLE = False
try:
    import qrcode
    import base64
    QR_AVAILABLE = True
except ImportError:
    pass

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
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'current_edit_id' not in st.session_state:
    st.session_state.current_edit_id = None
if 'current_edit_type' not in st.session_state:
    st.session_state.current_edit_type = None

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
    st.session_state.edit_mode = False
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

def start_edit(item_type, item_id):
    """Ενεργοποίηση λειτουργίας επεξεργασίας"""
    st.session_state.edit_mode = True
    st.session_state.current_edit_id = item_id
    st.session_state.current_edit_type = item_type

def cancel_edit():
    """Ακύρωση λειτουργίας επεξεργασίας"""
    st.session_state.edit_mode = False
    st.session_state.current_edit_id = None
    st.session_state.current_edit_type = None

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

# Tab 2: Νέα Παραλαβή (παραμένει ως έχει)
# Tab 3: Νέα Παραγγελία (παραμένει ως έχει)

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
    
    # Επιλογή υπάρχοντος για επεξεργασία
    if entities and not st.session_state.edit_mode:
        st.write("**Επεξεργασία υπάρχοντος:**")
        options = [f"{item['id']} - {item['name']}" for item in entities]
        options.insert(0, "Νέα εγγραφή")
        selected_option = st.selectbox("Επιλέξτε εγγραφή για επεξεργασία", options)
        
        if selected_option and selected_option != "Νέα εγγραφή":
            selected_id = int(selected_option.split(" - ")[0])
            selected_item = next((item for item in entities if item['id'] == selected_id), None)
            
            if selected_item and st.button("✏️ Επεξεργασία"):
                start_edit(entity_key, selected_id)
                st.rerun()
    
    # Φόρμα επεξεργασία/προσθήκη
    with st.form(f"{entity_key}_form"):
        if st.session_state.edit_mode and st.session_state.current_edit_type == entity_key:
            # Λειτουργία επεξεργασίας
            existing_item = next((item for item in entities if item['id'] == st.session_state.current_edit_id), None)
            if existing_item:
                st.info(f"Επεξεργασία: {existing_item['name']}")
                entity_id = st.number_input("ID", value=existing_item['id'], disabled=True)
                name = st.text_input("Όνομα", value=existing_item['name'])
                
                if entity_type == "Παραγωγοί":
                    quantity = st.number_input("Ποσότητα", value=existing_item.get('quantity', 0))
                    certifications_options = ["GlobalGAP", "GRASP", "Βιολογικό", "Βιοδυναμικό", "Συμβατικό", "ΟΠ"]
                    certifications = st.multiselect("Πιστοποιήσεις", certifications_options, default=existing_item.get('certifications', []))
                elif entity_type == "Πελάτες":
                    address = st.text_input("Διεύθυνση", value=existing_item.get('address', ''))
                    phone = st.text_input("Τηλέφωνο", value=existing_item.get('phone', ''))
                else:
                    contact = st.text_input("Πρόσωπο Επικοινωνίας", value=existing_item.get('contact', ''))
                    phone = st.text_input("Τηλέφωνο", value=existing_item.get('phone', ''))
            else:
                st.session_state.edit_mode = False
                st.rerun()
        else:
            # Λειτουργία προσθήκης
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
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Αποθήκευση")
        with col2:
            if st.session_state.edit_mode:
                if st.form_submit_button("❌ Ακύρωση"):
                    cancel_edit()
                    st.rerun()
        
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
            
            if st.session_state.edit_mode:
                # Ενημέρωση υπάρχοντος
                for i, item in enumerate(entities):
                    if item['id'] == st.session_state.current_edit_id:
                        entities[i] = new_entity
                        break
                st.success(f"✅ Ενημερώθηκε ο {entity_type[:-1]} #{entity_id}")
                cancel_edit()
            else:
                # Προσθήκη νέου
                entities.append(new_entity)
                st.success(f"✅ Προστέθηκε νέος {entity_type[:-1]} #{entity_id}")
            
            st.session_state[entity_key] = entities
            save_data({entity_key: entities})
            time.sleep(1)
            st.rerun()
    
    # Κατάλογος οντοτήτων με δυνατότητα διαγραφής
    st.subheader(f"Κατάλογος {entity_type}")
    if entities:
        for item in entities:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{item['name']}** (ID: {item['id']})")
                if entity_type == "Παραγωγοί":
                    st.write(f"Ποσότητα: {item.get('quantity', 0)} kg")
                elif entity_type == "Πελάτες":
                    st.write(f"Τηλ: {item.get('phone', '')}")
            with col2:
                if st.button("✏️ Επεξεργασία", key=f"edit_{item['id']}"):
                    start_edit(entity_key, item['id'])
                    st.rerun()
            with col3:
                if can_delete() and st.button("🗑️ Διαγραφή", key=f"del_{item['id']}"):
                    delete_item(entity_key, item['id'])
    else:
        st.info(f"Δεν υπάρχουν καταχωρημένοι {entity_type}")

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
        st.subheader(f"Επεξεργασία {data_type}")
        
        # Λίστα για επεξεργασία
        options = [f"{item['id']} - {item.get('variety', '')} ({item.get('receipt_date', item.get('date', ''))})" for item in items]
        selected_option = st.selectbox("Επιλέξτε για επεξεργασία/διαγραφή", options)
        
        if selected_option:
            selected_id = int(selected_option.split(" - ")[0])
            selected_item = next((item for item in items if item['id'] == selected_id), None)
            
            if selected_item:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Τρέχοντα Στοιχεία:**")
                    st.json(selected_item)
                
                with col2:
                    st.write("**Ενέργειες:**")
                    if st.button(f"Διαγραφή {data_type[:-1]} #{selected_id}", type="secondary"):
                        delete_item(item_key, selected_id)
                        st.rerun()
                    
                    st.warning("Για επεξεργασία, διαγράψτε και δημιουργήστε νέα εγγραφή με τα σωστά στοιχεία")
    else:
        st.info(f"Δεν υπάρχουν καταχωρημένες {data_type}")

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
        
        # Επεξεργασία χρηστών
        st.subheader("Επεξεργασία Χρηστών")
        user_options = list(st.session_state['users'].keys())
        selected_user = st.selectbox("Επιλέξτε χρήστη για επεξεργασία", user_options)
        
        if selected_user:
            user_data = st.session_state['users'][selected_user]
            
            with st.form("edit_user_form"):
                st.write(f"Επεξεργασία: {selected_user}")
                
                new_password = st.text_input("Νέος Κωδικός Πρόσβασης", type="password")
                confirm_password = st.text_input("Επιβεβαίωση Νέου Κωδικού", type="password")
                new_role = st.selectbox("Νέος Ρόλος", ["viewer", "editor", "admin"], 
                                      index=["viewer", "editor", "admin"].index(user_data['role']))
                new_fullname = st.text_input("Πλήρες Όνομα", value=user_data['full_name'])
                
                col1, col2 = st.columns(2)
                with col1:
                    update_submitted = st.form_submit_button("💾 Ενημέρωση Χρήστη")
                with col2:
                    if st.form_submit_button("🗑️ Διαγραφή Χρήστη"):
                        if selected_user != 'admin':  # Αποτροπή διαγραφής admin
                            del st.session_state['users'][selected_user]
                            save_data({'users': st.session_state['users']})
                            st.success(f"✅ Ο χρήστης {selected_user} διαγράφηκε!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Δεν μπορείτε να διαγράψετε τον admin user!")
                
                if update_submitted:
                    if new_password:
                        if new_password != confirm_password:
                            st.error("Οι κωδικοί δεν ταιριάζουν")
                        else:
                            user_data['password'] = hash_password(new_password)
                    
                    user_data['role'] = new_role
                    user_data['full_name'] = new_fullname
                    
                    st.session_state['users'][selected_user] = user_data
                    save_data({'users': st.session_state['users']})
                    st.success(f"✅ Ο χρήστης {selected_user} ενημερώθηκε!")
                    time.sleep(1)
                    st.rerun()

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