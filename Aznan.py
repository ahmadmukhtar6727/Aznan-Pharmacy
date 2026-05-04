import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import os

# --- 1. DEFINE THE FUNCTION FIRST ---
def create_pdf_receipt(sale_data):
    # Dynamic height calculation for long lists
    dynamic_height = 130 + (len(sale_data['items']) * 10)
    pdf = FPDF(unit='mm', format=[80, dynamic_height])
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=5)

    # --- 1. LOGO SECTION (Centered & Small) ---
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        # x=30, w=20 centers a small 20mm logo on 80mm paper
        pdf.image(logo_path, x=28, y=5, w=25)
        pdf.ln(22)
    else:
        pdf.ln(5)

    # --- 2. HEADER SECTION ---
    # Pharmacy Name: Bigger & Bold
    pdf.set_font("Courier", "B", 16)
    pdf.cell(60, 8, "AZNAN PHARMACY", ln=True, align='C')
    
    # Address: Full & Wrapped (to handle long text)
    pdf.set_font("Courier", "", 8)
    # multi_cell allows the address to wrap to the next line automatically
    pdf.multi_cell(58, 3, "IBB Way, Bakin Kasuwa, Opposite Eye Center, Katsina, Katsina State, Nigeria.", align='C')
    
    # Phone Numbers
    pdf.cell(58, 3, "08167899122, 07039522767, 08102716591", ln=True, align='C')
    
    # Date and Time on the same line
    pdf.set_font("Courier", "", 7)
    now = datetime.now().strftime('%d/%m/%Y   %H:%M')
    pdf.cell(58, 3, f"Date/Time: {now}", ln=True, align='C')
    pdf.ln(2)

    # --- 3. STAFF & CUSTOMER INFO ---
    pdf.set_font("Courier", "B", 8)
    # Left side: Staff & Customer | Right side: Payment Status
    curr_y = pdf.get_y()
    pdf.text(8, curr_y, f"Staff: {st.session_state.user}")
    pdf.set_font("Courier", "B", 8)
    pdf.text(58, curr_y, f"[{sale_data['status'].upper()}]") # PAID or CREDIT
    
    pdf.ln(4)
    pdf.set_font("Courier", "", 9)
    pdf.cell(60, 5, f"Customer: {sale_data['customer']}", ln=True)
    pdf.ln(2)

    # --- 4. TABLE (Full Design with Borders) ---
    pdf.set_font("Courier", "B", 8)
    # S/N (8mm), Drug (30mm), Qty (8mm), Price (14mm)
    pdf.cell(7, 6, "S/N", 1, 0, 'C')
    pdf.cell(31, 6, "Drug Name", 1, 0, 'C')
    pdf.cell(10, 6, "Qty", 1, 0, 'C')
    pdf.cell(12, 6, "Price", 1, 1, 'C')
    
    pdf.set_font("Courier", "", 8)
    for i, item in enumerate(sale_data['items'], 1):
        # We use cell height of 7 for 20-30 items
        pdf.cell(7, 7, str(i), 1, 0, 'C')
        pdf.cell(31, 7, item['item'][:18], 1, 0, 'L')
        pdf.cell(10, 7, str(item['qty']), 1, 0, 'C')
        pdf.cell(12, 7, f"{item['subtotal']:,.0f}", 1, 1, 'R')

    # --- 5. BOTTOM (Totals & Discount) ---
    pdf.ln(1) # Tiny gap
    pdf.set_font("Courier", "B", 6)
    subtotal = sale_data['total'] + sale_data['discount']
    
    # Height reduced to 4 for tight spacing
    pdf.cell(30, 4, "Total     :", 0, 0, 'L')
    pdf.cell(30, 4, f"{subtotal:,.2f}", 0, 1, 'L')
    
    pdf.cell(30, 4, "Discount  :", 0, 0, 'L')
    pdf.cell(30, 4, f"{sale_data['discount']:,.2f}", 0, 1, 'L')
    
    # Very thin dash line
    pdf.cell(60, 1, "-" * 25, ln=True)
    
    # Final total with minimal extra padding
    pdf.set_font("Courier", "B", 7)
    pdf.cell(30, 5, "Net Total :", 0, 0, 'L') 
    pdf.cell(30, 5, f"{sale_data['total']:,.2f}", 0, 1, 'L')

    # --- 6. CENTERED FOOTER ---
    pdf.ln(5)
    pdf.set_font("Courier", "B", 8)
    pdf.cell(60, 5, "THANK YOU!", ln=True, align='C')
    pdf.set_font("Courier", "I", 7)
    pdf.cell(60, 4, "Wishing you a quick recovery.", ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')

DB_NAME = "Aznan_Pro_Final.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        # Users Table
        conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)")
        # Products Table (Inventory)
        conn.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, 
            buying_price REAL, retail_price REAL, wholesale_price REAL, 
            stock_qty INTEGER, expiry_date TEXT, low_stock_limit INTEGER DEFAULT 5)""")
        # Sales Table
        conn.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, quantity INTEGER, 
            total_price REAL, profit REAL, date TEXT, staff_name TEXT)""")
        # Expenses Table
        conn.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, amount REAL, date TEXT)")
        # Debts Table
        conn.execute("CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, amount REAL, status TEXT, date TEXT)")
        
        # Initial Admin Account
        if not conn.execute("SELECT * FROM users WHERE username='admin'").fetchone():
            conn.execute("INSERT INTO users VALUES ('admin', 'admin123', 'Admin')")
            conn.commit()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            description TEXT,
            amount REAL,
            date TEXT
        )
    """)

        # Create table if it doesn't exist at all
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                description TEXT,
                amount REAL,
                date TEXT
            )
        """)
        
        # Check if 'category' column exists (Safety check)
        cursor = conn.execute("PRAGMA table_info(expenses)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'category' not in columns:
            conn.execute("ALTER TABLE expenses ADD COLUMN category TEXT")

init_db()

# --- LOGIN SECTION ---
if not st.session_state.get('logged_in'):
    st.title("🔐 Aznan Pharmacy Login")
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login", use_container_width=True):
        with sqlite3.connect(DB_NAME) as conn:
            # We fetch both the password AND the role
            user_data = conn.execute("SELECT role FROM users WHERE username = ? AND password = ?", 
                                    (user_input, pass_input)).fetchone()
        
        if user_data:
            st.session_state.logged_in = True
            st.session_state.user = user_input
            st.session_state.role = user_data[0] # This stores 'Admin' or 'Staff'
            st.success(f"Welcome, {user_input}!")
            st.rerun()
        else:
            st.error("Invalid Username or Password")
    st.stop() # Stops the rest of the app from loading until login is successful

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title(f"💊 Aznan Pharmacy")
    st.write(f"Logged in as: **{st.session_state.user}** ({st.session_state.role})")
    
    # Define menu options based on role
    if st.session_state.role == "Admin":
        menu_options = ["📊 Dashboard", "📦 Inventory", "🛒 POS/Sales", "💸 Expenses & Debt", "⚙️ Staff Mgmt", "📊 Report"]
    else:
        # Staff can only see Inventory (List only) and POS/Sales
        menu_options = ["📦 Inventory", "🛒 POS/Sales", "💸 Expenses & Debt"]
    
    choice = st.selectbox("Menu", menu_options)
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- LOGIN SECTION ---
if not st.session_state.get('logged_in'):
    st.title("🔐 Aznan Pharmacy Login")
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login", use_container_width=True):
        with sqlite3.connect(DB_NAME) as conn:
            # We fetch both the password AND the role
            user_data = conn.execute("SELECT role FROM users WHERE username = ? AND password = ?", 
                                    (user_input, pass_input)).fetchone()
        
        if user_data:
            st.session_state.logged_in = True
            st.session_state.user = user_input
            st.session_state.role = user_data[0] # This stores 'Admin' or 'Staff'
            st.success(f"Welcome, {user_input}!")
            st.rerun()
        else:
            st.error("Invalid Username or Password")
    st.stop() # Stops the rest of the app from loading until login is successful

# --- MAIN LOGIC ---
if choice == "📊 Dashboard":
    # Paste the Dashboard code I gave you here...
    st.title("📊 Business Analytics")
    
    # 1. Fetch Data from all tables
    with sqlite3.connect(DB_NAME) as conn:
        sales_df = pd.read_sql("SELECT * FROM sales", conn)
        exp_df = pd.read_sql("SELECT * FROM expenses", conn)
        debt_df = pd.read_sql("SELECT * FROM debts", conn)
        prod_df = pd.read_sql("SELECT * FROM products", conn)

    # 2. Perform Calculations
    # Revenue & Gross Profit
    total_revenue = sales_df['total_price'].sum() if not sales_df.empty else 0.0
    gross_profit = sales_df['profit'].sum() if not sales_df.empty else 0.0
    
    # Expenses & Net Profit
    total_expenses = exp_df['amount'].sum() if not exp_df.empty else 0.0
    net_profit = gross_profit - total_expenses
    
    # Debts (Pending)
    pending_debts = debt_df[debt_df['status'] == 'Pending']['amount'].sum() if not debt_df.empty else 0.0
    
    # Daily Profit (Filter sales from today's date)
    today_str = datetime.now().strftime('%Y-%m-%d')
    daily_sales = sales_df[sales_df['date'] == today_str]
    daily_profit = daily_sales['profit'].sum() if not daily_sales.empty else 0.0

    # 3. Display 6 Metrics in two rows
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    row1_col1.metric("Revenue", f"₦{total_revenue:,.2f}")
    row1_col2.metric("Gross Profit", f"₦{gross_profit:,.2f}")
    row1_col3.metric("Net Profit", f"₦{net_profit:,.2f}")

    st.markdown("---") # Visual separator

    row2_col1, row2_col2, row2_col3 = st.columns(3)
    row2_col1.metric("Pending Debt", f"₦{pending_debts:,.2f}")
    row2_col2.metric("Total Expenses", f"₦{total_expenses:,.2f}")
    row2_col3.metric("Daily Profit", f"₦{daily_profit:,.2f}", delta=f"₦{daily_profit:,.2f}")

    st.divider()

    # 4. Alerts Section
    st.subheader("🚨 Priority Alerts")
    
    col_alert1, col_alert2 = st.columns(2)
    
    with col_alert1:
        st.write("### 📦 Stock Alerts")
        # Items below threshold (default 5)
        low_stock = prod_df[prod_df['stock_qty'] <= 5]
        if not low_stock.empty:
            st.warning(f"You have {len(low_stock)} items low on stock!")
            st.dataframe(low_stock[['name', 'stock_qty']], use_container_width=True)
        else:
            st.success("All stock levels are healthy.")

    with col_alert2:
        st.write("### ⌛ Expiry Alerts")
        # Items expiring in the next 30 days
        if not prod_df.empty:
            prod_df['expiry_date'] = pd.to_datetime(prod_df['expiry_date'])
            soon = datetime.now() + timedelta(days=30)
            expiring_items = prod_df[prod_df['expiry_date'] <= soon]
            
            if not expiring_items.empty:
                st.error(f"{len(expiring_items)} items expiring within 30 days!")
                st.dataframe(expiring_items[['name', 'expiry_date']], use_container_width=True)
            else:
                st.success("No upcoming expirations.")
        else:
            st.info("No products in inventory.")

elif choice == "📦 Inventory":
    st.title("📦 Inventory Management")
    
    # --- ROLE-BASED TAB LOGIC ---
    if st.session_state.role == "Admin":
        # Admin sees all 3 options in one row of tabs
        tab1, tab2, tab3 = st.tabs(["➕ Add New Stock", "📋 View Inventory", "🗑️ Remove/Edit"])
    else:
        # Staff ONLY sees the View Inventory tab
        tab2 = st.container()
        st.info("Staff Access: View Only Mode")
        tab1 = None # Disable Add for staff
        tab3 = None # Disable Delete for staff

    # --- TAB 1: ADD NEW STOCK (Admin Only) ---
    if tab1 and st.session_state.role == "Admin":
        with tab1:
            st.subheader("Add New Product")
            with st.form("stock_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                p_name = col1.text_input("Product Name")
                p_unit = col2.selectbox("Unit Type", ["Card", "Bottle", "Single", "Sachet", "Box", "Injection"])
                p_cat = col1.selectbox("Category", ["Tablets", "Syrup", "Analgesics", "Antibiotics", "Other"])
                exp_date = col2.date_input("Expiry Date", min_value=datetime.now())
                
                b_price = col1.number_input("Buying Price (₦)", min_value=0.0)
                w_price = col2.number_input("Wholesale Price (₦)", min_value=0.0)
                r_price = col1.number_input("Retail Price (₦)", min_value=0.0)
                
                qty = col2.number_input("Quantity in Stock", min_value=0, step=1)
                limit = col1.number_input("Low Stock Alert Level", min_value=1, value=5)
                
                if st.form_submit_button("✅ Add Product"):
                    if p_name:
                        full_name = f"{p_name} ({p_unit})"
                        with sqlite3.connect(DB_NAME) as conn:
                            conn.execute("""
                                INSERT INTO products (name, category, buying_price, wholesale_price, retail_price, stock_qty, expiry_date, low_stock_limit) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (full_name, p_cat, b_price, w_price, r_price, qty, str(exp_date), limit))
                            conn.commit()
                        st.success(f"Added {full_name}!")
                        st.rerun()

    # --- TAB 2: VIEW INVENTORY (Everyone) ---
    with tab2:
        st.subheader("📋 Current Stock List")
        with sqlite3.connect(DB_NAME) as conn:
            # We show everything except the Buying Price to Staff for privacy
            if st.session_state.role == "Admin":
                query = "SELECT name, category, stock_qty, buying_price, wholesale_price, retail_price, expiry_date FROM products"
            else:
                query = "SELECT name, category, stock_qty, wholesale_price, retail_price, expiry_date FROM products"
            
            inventory_df = pd.read_sql(query, conn)
        
        if not inventory_df.empty:
            # Highlights low stock in the table
            st.dataframe(inventory_df.style.highlight_min(subset=['stock_qty'], color='#ffcccc'), use_container_width=True)
        else:
            st.info("The inventory is currently empty.")

    # --- TAB 3: REMOVE/EDIT (Admin Only) ---
    if tab3 and st.session_state.role == "Admin":
        with tab3:
            st.subheader("🗑️ Delete Product")
            with sqlite3.connect(DB_NAME) as conn:
                prod_list = pd.read_sql("SELECT name FROM products", conn)
            
            if not prod_list.empty:
                delete_target = st.selectbox("Select Product to Remove", prod_list['name'].tolist())
                if st.button("❌ Confirm Permanent Deletion"):
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute("DELETE FROM products WHERE name = ?", (delete_target,))
                        conn.commit()
                    st.error(f"Removed {delete_target} from system.")
                    st.rerun()

elif choice == "⚙️ Staff Mgmt":
    st.title("⚙️ Staff & Security Management")
    
    # 1. Overview Table
    st.subheader("Current System Users")
    with sqlite3.connect(DB_NAME) as conn:
        users_df = pd.read_sql("SELECT username, role FROM users", conn)
    st.dataframe(users_df, use_container_width=True)

    st.divider()

    # 2. Tabs for different actions
    tab_add, tab_edit = st.tabs(["➕ Add New Staff", "🔐 Password & Account Control"])

    with tab_add:
        st.subheader("Create New Account")
        with st.form("add_user_form", clear_on_submit=True):
            new_username = st.text_input("Username")
            new_password = st.text_input("Temporary Password", type="password")
            new_role = st.selectbox("Assign Role", ["Staff", "Admin"])
            
            submit_user = st.form_submit_button("Register User")
            
            if submit_user:
                if new_username and new_password:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                                         (new_username, new_password, new_role))
                            conn.commit()
                        st.success(f"Account for '{new_username}' created successfully!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("This username already exists. Please choose another.")
                else:
                    st.warning("Please fill in both username and password.")

    with tab_edit:
        st.subheader("Manage Existing Accounts")
        
        # Select user to modify
        target_user = st.selectbox("Select User to Modify", users_df['username'].tolist())
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Change Password")
            new_pwd = st.text_input("Enter New Password", type="password", key="new_pwd_input")
            if st.button("Update Password"):
                if new_pwd:
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute("UPDATE users SET password = ? WHERE username = ?", (new_pwd, target_user))
                        conn.commit()
                    st.success(f"Password for {target_user} updated!")
                else:
                    st.error("Please enter a new password.")

        with col2:
            st.write("### Delete Account")
            st.warning("Warning: This action cannot be undone.")
            if st.button("❌ Permanent Delete"):
                # Safety check: Prevent Admin from deleting their own current session account
                if target_user == st.session_state.user:
                    st.error("Security Alert: You cannot delete your own account while logged in!")
                elif target_user == "admin":
                    st.error("Security Alert: The Master Admin account cannot be deleted.")
                else:
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute("DELETE FROM users WHERE username = ?", (target_user,))
                        conn.commit()
                    st.success(f"Account '{target_user}' has been removed.")
                    st.rerun()

elif choice == "🛒 POS/Sales":
    st.title("🛒 Point of Sale")

    # Initialize session states for the PDF
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'receipt_ready' not in st.session_state:
        st.session_state.receipt_ready = False

    col_input, col_basket = st.columns([1, 1.2])

    # --- LEFT: SELECTION ---
    with col_input:
        st.subheader("Select Products")
        with sqlite3.connect(DB_NAME) as conn:
            products_df = pd.read_sql("SELECT name, retail_price, wholesale_price, stock_qty, buying_price FROM products", conn)
        
        selected_prod = st.selectbox("Search Item", products_df['name'].tolist())
        prod_info = products_df[products_df['name'] == selected_prod].iloc[0]
        
        price_mode = st.radio("Price Mode", ["Retail", "Wholesale"], horizontal=True)
        current_price = prod_info['retail_price'] if price_mode == "Retail" else prod_info['wholesale_price']
        
        qty = st.number_input("Quantity", min_value=1, max_value=int(prod_info['stock_qty']), step=1)
        
        if st.button("➕ Add to Basket", use_container_width=True):
            st.session_state.cart.append({
                "item": selected_prod,
                "unit_price": current_price,
                "buying_price": prod_info['buying_price'],
                "qty": qty,
                "subtotal": current_price * qty
            })
            st.rerun()

    # --- RIGHT: BASKET & PDF DOWNLOAD ---
    with col_basket:
        st.subheader("🧺 Shopping Basket")
        if st.session_state.cart:
            df_display = pd.DataFrame(st.session_state.cart)
            st.table(df_display[['item', 'qty', 'unit_price', 'subtotal']])
            
            raw_total = sum(item['subtotal'] for item in st.session_state.cart)
            
            st.markdown("---")
            final_discount = st.number_input("Total Discount (₦)", min_value=0.0, step=5.0)
            grand_total = raw_total - final_discount
            
            st.markdown(f"### Total: <span style='color:green'>₦{grand_total:,.2f}</span>", unsafe_allow_html=True)
            
            customer_name = st.text_input("Customer Name")
            payment_status = st.selectbox("Payment Type", ["Paid", "Credit"])

            b1, b2 = st.columns(2)
            if b1.button("🗑️ Empty", use_container_width=True):
                st.session_state.cart = []
                st.rerun()

            if b2.button("✅ Finalize & Prepare PDF", use_container_width=True):
                with sqlite3.connect(DB_NAME) as conn:
                    discount_ratio = final_discount / raw_total if raw_total > 0 else 0
                    
                    for item in st.session_state.cart:
                        item_discount = item['subtotal'] * discount_ratio
                        final_item_price = item['subtotal'] - item_discount
                        item_profit = final_item_price - (item['buying_price'] * item['qty'])
                        
                        conn.execute("""
                            INSERT INTO sales (product_name, quantity, total_price, profit, date, staff_name)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (item['item'], item['qty'], final_item_price, item_profit, 
                              datetime.now().strftime('%Y-%m-%d'), st.session_state.user))
                        
                        conn.execute("UPDATE products SET stock_qty = stock_qty - ? WHERE name = ?", (item['qty'], item['item']))
                        
                    if payment_status == "Credit":
                        conn.execute("INSERT INTO debts (customer, amount, status, date) VALUES (?, ?, ?, ?)",
                                    (customer_name if customer_name else "Guest", grand_total, "Pending", datetime.now().strftime('%Y-%m-%d')))
                    conn.commit()
                
                # Create the PDF data
                sale_info = {
                    "customer": customer_name if customer_name else "Cash Customer",
                    "items": list(st.session_state.cart),
                    "total": grand_total,
                    "discount": final_discount,
                    "status": payment_status
                }
                
                # Run the FPDF function we built earlier
                st.session_state.last_pdf = create_pdf_receipt(sale_info)
                st.session_state.receipt_ready = True
                st.session_state.cart = [] 
                st.success("Sale Saved! Click download below.")

        # --- THE DOWNLOAD BUTTON ---
        if st.session_state.receipt_ready:
            st.download_button(
                label="📥 Download 80mm PDF Receipt",
                data=st.session_state.last_pdf,
                file_name=f"Receipt_{datetime.now().strftime('%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            if st.button("Start New Sale"):
                st.session_state.receipt_ready = False
                st.rerun()

elif choice == "💸 Expenses & Debt":
    st.title("💸 Financial Management")
    
    tab1, tab2 = st.tabs(["📉 Business Expenses", "🤝 Debt Management"])

    # --- TAB 1: EXPENSES ---
    with tab1:
        st.subheader("Record New Expense")
        with st.form("expense_form", clear_on_submit=True):
            cat = st.selectbox("Category", ["Staff Salary", "Utilities", "Transport", "Rent", "Maintenance", "Other"])
            desc = st.text_input("Description (Details)")
            amt = st.number_input("Amount (₦)", min_value=0.0, step=100.0)
            if st.form_submit_button("Log Expense"):
                with sqlite3.connect(DB_NAME) as conn:
                    conn.execute("INSERT INTO expenses (category, description, amount, date) VALUES (?,?,?,?)",
                                (cat, desc, amt, datetime.now().strftime('%Y-%m-%d')))
                st.success("Expense recorded!")

        st.markdown("---")
        st.subheader("Recent Expenses")
        with sqlite3.connect(DB_NAME) as conn:
            exp_df = pd.read_sql("SELECT * FROM expenses ORDER BY id DESC LIMIT 10", conn)
            st.dataframe(exp_df, use_container_width=True)

    # --- TAB 2: DEBT MANAGEMENT ---
    with tab2:
        st.subheader("🤝 Customer Debt Ledger")
        
        # 1. Fetch the latest debt data
        with sqlite3.connect(DB_NAME) as conn:
            debt_df = pd.read_sql("SELECT * FROM debts WHERE amount > 0", conn)
        
        if not debt_df.empty:
            # Display current debts
            st.dataframe(debt_df.style.format({"amount": "₦{:,.2f}"}), use_container_width=True)
            
            st.markdown("---")
            st.subheader("Update Debt Status")
            
            # 2. Select customer
            # We use a combined string to ensure we get the right ID
            debt_options = {f"{row['customer']} (₦{row['amount']})": row['id'] for _, row in debt_df.iterrows()}
            selected_label = st.selectbox("Select Customer to Update", options=list(debt_options.keys()))
            debt_id = debt_options[selected_label]
            
            # Get specific debt details
            current_debt_row = debt_df[debt_df['id'] == debt_id].iloc[0]
            current_balance = float(current_debt_row['amount'])
            
            action = st.radio("What happened?", ["Partial Payment", "Full Settlement", "Product Return"], horizontal=True)
            
            # --- ACTION LOGIC ---
            if action == "Partial Payment":
                pay_amt = st.number_input("Amount Paid (₦)", min_value=0.0, max_value=current_balance, step=50.0)
                if st.button("Confirm Payment"):
                    new_balance = current_balance - pay_amt
                    with sqlite3.connect(DB_NAME) as conn:
                        # Update the amount
                        conn.execute("UPDATE debts SET amount = ? WHERE id = ?", (new_balance, debt_id))
                        conn.commit() # Save changes
                    st.success(f"Payment recorded! Remaining: ₦{new_balance:,.2f}")
                    st.rerun()

            elif action == "Full Settlement":
                if st.button("Clear This Debt Completely"):
                    with sqlite3.connect(DB_NAME) as conn:
                        # Option A: Delete the record
                        # conn.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
                        # Option B: Set amount to 0 (Better for records)
                        conn.execute("UPDATE debts SET amount = 0 WHERE id = ?", (debt_id,))
                        conn.commit()
                    st.balloons()
                    st.success("Debt marked as fully paid!")
                    st.rerun()

            elif action == "Product Return":
                return_val = st.number_input("Value of Product Returned (₦)", min_value=0.0, max_value=current_balance)
                if st.button("Apply Return Credit"):
                    new_balance = current_balance - return_val
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute("UPDATE debts SET amount = ? WHERE id = ?", (new_balance, debt_id))
                        conn.commit()
                    st.success(f"Product returned. New balance: ₦{new_balance:,.2f}")
                    st.rerun()
        else:
            st.info("No active debts found in the system.")

elif choice == "📊 Report":
    st.title("📊 Financial Reports")
    
    report_type = st.radio("Select Report Range", ["Daily Report", "Monthly Report"], horizontal=True)
    
    # Define Date Range based on selection
    if report_type == "Daily Report":
        target_date = st.date_input("Select Date", datetime.now())
        date_str = target_date.strftime('%Y-%m-%d')
        query_filter = f"date = '{date_str}'"
        report_title = f"Daily Report - {date_str}"
    else:
        month_list = ["January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"]
        selected_month = st.selectbox("Select Month", month_list, index=datetime.now().month - 1)
        month_idx = f"{month_list.index(selected_month) + 1:02d}"
        year_str = datetime.now().strftime('%Y')
        query_filter = f"date LIKE '{year_str}-{month_idx}-%'"
        report_title = f"Monthly Report - {selected_month} {year_str}"

    # --- DATA AGGREGATION ---
    with sqlite3.connect(DB_NAME) as conn:
        # Sum Sales
        sales_data = pd.read_sql(f"SELECT SUM(total_price) as total, SUM(profit) as profit FROM sales WHERE {query_filter}", conn)
        total_sales = sales_data['total'].iloc[0] or 0.0
        total_profit = sales_data['profit'].iloc[0] or 0.0
        
        # Sum Expenses
        exp_data = pd.read_sql(f"SELECT SUM(amount) as total FROM expenses WHERE {query_filter}", conn)
        total_expenses = exp_data['total'].iloc[0] or 0.0
        
        # Details Tables
        detailed_sales = pd.read_sql(f"SELECT product_name, quantity, total_price, date FROM sales WHERE {query_filter}", conn)
        detailed_expenses = pd.read_sql(f"SELECT category, description, amount, date FROM expenses WHERE {query_filter}", conn)

    # --- DISPLAY SUMMARY CARDS ---
    net_income = total_profit - total_expenses
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gross Sales", f"₦{total_sales:,.2f}")
    col2.metric("Total Expenses", f"₦{total_expenses:,.2f}", delta_color="inverse")
    col3.metric("Net Profit", f"₦{net_income:,.2f}")

    # --- DOWNLOAD SECTION ---
    st.markdown("---")
    if st.button("📄 Generate Report PDF"):
        # Create a simple PDF Report
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "AZNAN PHARMACY - FINANCIAL REPORT", ln=True, align='C')
        pdf.set_font("Arial", "", 12)
        pdf.cell(190, 10, report_title, ln=True, align='C')
        pdf.ln(10)
        
        # Summary Table
        pdf.set_font("Arial", "B", 12)
        pdf.cell(95, 10, "Description", 1)
        pdf.cell(95, 10, "Amount (N)", 1, ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(95, 10, "Gross Sales", 1)
        pdf.cell(95, 10, f"{total_sales:,.2f}", 1, ln=True)
        pdf.cell(95, 10, "Total Expenses", 1)
        pdf.cell(95, 10, f"{total_expenses:,.2f}", 1, ln=True)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(95, 10, "Net Profit", 1)
        pdf.cell(95, 10, f"{net_income:,.2f}", 1, ln=True)
        
        report_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button(
            label="📥 Download PDF Report",
            data=report_bytes,
            file_name=f"Report_{date_str if report_type == 'Daily Report' else selected_month}.pdf",
            mime="application/pdf"
        )

    # --- DATA TABLES ---
    with st.expander("View Sales Details"):
        st.dataframe(detailed_sales, use_container_width=True)
    with st.expander("View Expense Details"):
        st.dataframe(detailed_expenses, use_container_width=True)
