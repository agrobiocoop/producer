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
import qrcode
import base64

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

# Συνάρτηση δημιουργίας QR code
def generate_qr_code(data, filename="qrcode.png"):
    """Δημιουργία QR code από δεδομένα"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    return filename

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Δημιουργία link για download"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{bin_file}">{file_label}</a>'
    return href

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
                "order_id": order_id,
                "shipped_to_id": shipped_to_id,  # ΝΕΟ ΠΕΔΙΟ
                "shipped_to": shipped_to if shipped_to != "Κανένας" else None,  # ΝΕΟ ΠΕΔΙΟ
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
            
            # ΔΗΜΙΟΥΡΓΙΑ QR CODE
            qr_data = f"ΠΑΡΑΛΑΒΗ #{receipt_id}\nΠαραγωγός: {selected_producer}\nΗμερομηνία: {receipt_date}\nΠοσότητα: {total_kg} kg\nΑξία: {total_value:.2f}€"
            qr_filename = generate_qr_code(qr_data, f"receipt_{receipt_id}_qrcode.png")
            
            st.success("📲 QR Code δημιουργήθηκε!")
            st.image(qr_filename, caption=f"QR Code για Παραλαβή #{receipt_id}", width=200)
            
            # DOWNLOAD LINK ΓΙΑ QR CODE
            st.markdown(get_binary_file_downloader_html(qr_filename, f"Κατεβάστε QR Code για Παραλαβή #{receipt_id}"), unsafe_allow_html=True)
            
            time.sleep(3)
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
            
            # ΔΗΜΙΟΥΡΓΙΑ QR CODE
            qr_data = f"ΠΑΡΑΓΓΕΛΙΑ #{order_id}\nΠελάτης: {customer_name}\nΗμερομηνία: {order_date}\nΠοσότητα: {total_kg} kg\nΑξία: {total_value:.2f}€"
            qr_filename = generate_qr_code(qr_data, f"order_{order_id}_qrcode.png")
            
            st.success("📲 QR Code δημιουργήθηκε!")
            st.image(qr_filename, caption=f"QR Code για Παραγγελία #{order_id}", width=200)
            
            # DOWNLOAD LINK ΓΙΑ QR CODE
            st.markdown(get_binary_file_downloader_html(qr_filename, f"Κατεβάστε QR Code για Παραγγελία #{order_id}"), unsafe_allow_html=True)
            
            time.sleep(3)
            st.rerun()

# Tab 4: Αναφορές
with current_tab[3]:
    st.header("📈 Αναφορές και Εκτυπώσεις")
    
    # Προσθήκη QR code generation για υπάρχουσες εγγραφές
    st.subheader("📲 Δημιουργία QR Code για υπάρχουσες εγγραφές")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Για Παραλαβές:**")
        if st.session_state['receipts']:
            receipt_options = [f"{r['id']} - {r.get('variety', '')} ({r['receipt_date']})" for r in st.session_state['receipts']]
            selected_receipt = st.selectbox("Επιλέξτε Παραλαβή", options=receipt_options)
            if selected_receipt and st.button("📲 QR για Παραλαβή"):
                receipt_id = int(selected_receipt.split(" - ")[0])
                receipt = next((r for r in st.session_state['receipts'] if r['id'] == receipt_id), None)
                if receipt:
                    qr_data = f"ΠΑΡΑΛΑΒΗ #{receipt['id']}\nΗμερομηνία: {receipt['receipt_date']}\nΠοσότητα: {receipt.get('total_kg', 0)} kg\nΑξία: {receipt.get('total_value', 0):.2f}€"
                    qr_filename = generate_qr_code(qr_data, f"receipt_{receipt_id}_qrcode.png")
                    st.image(qr_filename, caption=f"QR Code για Παραλαβή #{receipt_id}", width=200)
                    st.markdown(get_binary_file_downloader_html(qr_filename, f"Κατεβάστε QR Code"), unsafe_allow_html=True)
    
    with col2:
        st.write("**Για Παραγγελίες:**")
        if st.session_state['orders']:
            order_options = [f"{o['id']} - {o.get('customer', '')} ({o['date']})" for o in st.session_state['orders']]
            selected_order = st.selectbox("Επιλέξτε Παραγγελία", options=order_options)
            if selected_order and st.button("📲 QR για Παραγγελία"):
                order_id = int(selected_order.split(" - ")[0])
                order = next((o for o in st.session_state['orders'] if o['id'] == order_id), None)
                if order:
                    qr_data = f"ΠΑΡΑΓΓΕΛΙΑ #{order['id']}\nΠελάτης: {order.get('customer', '')}\nΗμερομηνία: {order['date']}\nΠοσότητα: {order.get('total_kg', 0)} kg\nΑξία: {order.get('total_value', 0):.2f}€"
                    qr_filename = generate_qr_code(qr_data, f"order_{order_id}_qrcode.png")
                    st.image(qr_filename, caption=f"QR Code για Παραγγελία #{order_id}", width=200)
                    st.markdown(get_binary_file_downloader_html(qr_filename, f"Κατεβάστε QR Code"), unsafe_allow_html=True)

# Τα υπόλοιπα tabs παραμένουν ως έχουν...

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