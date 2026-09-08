import streamlit as st
import pandas as pd
import pydeck as pdk
import random
from supabase import create_client

# Page Config
st.set_page_config(
    page_title="FreshVeggies Express",
    page_icon="🥦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Google Font (Poppins) & UI Polishing
st.markdown("""
<style>
    /* Import Google Font - Poppins */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    /* Apply Poppins to every text element in Streamlit */
    html, body, [class*="st-"], .stMarkdown, button, input, select, textarea {
        font-family: 'Poppins', sans-serif !important;
    }

    .main-header {
        font-size: 2.2rem;
        color: #2E7D32;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #555555;
        margin-bottom: 20px;
    }
    .price-tag {
        font-size: 1.2rem;
        color: #2E7D32;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def fetch_orders():
    response = supabase.table("orders").select("*").execute()
    data = response.data
    if not data:
        return pd.DataFrame(columns=["id", "item", "customer", "lat", "lon", "status", "driver", "price"])
    return pd.DataFrame(data)

def fetch_drivers():
    response = supabase.table("users").select("username").eq("role", "Driver").execute()
    data = response.data
    if not data:
        return ["Unassigned"]
    return [d["username"] for d in data]

def login_user(username, password):
    response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
    if response.data:
        return response.data[0]
    return None

# Manage Login Session State
if "user" not in st.session_state:
    st.session_state["user"] = None

# Sidebar Branding
st.sidebar.title("🥦 FreshVeggies")
portal_type = st.sidebar.radio("Navigation", ["🛒 Customer Shop", "🔐 Staff Login"])

df_orders = fetch_orders()

# --- 1. VISUAL CUSTOMER SHOP ---
if portal_type == "🛒 Customer Shop":
    st.markdown('<p class="main-header">🥦 FreshVeggies Market</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Select farm-fresh vegetable bundles delivered directly to your door in Kumasi.</p>', unsafe_allow_html=True)
    
    # # Products Catalog with Ultra-Reliable Static Image Links
    products = [
        {
            "name": "Tomato Basket",
            "price": 45,
            "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Tomato_je.jpg",
            "desc": "Fresh, ripe local tomatoes perfect for stews and fresh salads."
        },
        {
            "name": "Leafy Greens Mix",
            "price": 30,
            "img": "https://upload.wikimedia.org/wikipedia/commons/b/b5/Assorted_vegetables_display.jpg",
            "desc": "Crisp lettuce, spinach, and fresh local green vegetables."
        },
        {
            "name": "Onion & Pepper Combo",
            "price": 50,
            "img": "https://upload.wikimedia.org/wikipedia/commons/1/15/Red_Onion_and_Chili_Pepper.jpg",
            "desc": "Essential cooking pack with fresh red onions and scotch bonnet peppers."
        }
    ]

    # Render Product Cards Grid
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    st.subheader("📝 Customer Delivery Details")
    cust_name = st.text_input("Your Name / Phone Number (for delivery confirmation)")

    for idx, prod in enumerate(products):
        with cols[idx]:
            st.image(prod["img"], use_container_width=True)
            st.markdown(f"### {prod['name']}")
            st.markdown(prod["desc"])
            st.markdown(f'<p class="price-tag">GH₵ {prod["price"]}.00</p>', unsafe_allow_html=True)
            
            if st.button(f"Order {prod['name']}", key=f"btn_{idx}"):
                if not cust_name:
                    st.warning("Please enter your name or phone number above before placing an order.")
                else:
                    new_order = {
                        "item": prod["name"],
                        "customer": cust_name,
                        "lat": 6.688 + random.uniform(-0.015, 0.015),
                        "lon": -1.624 + random.uniform(-0.015, 0.015),
                        "status": "Pending",
                        "driver": "Unassigned",
                        "price": prod["price"]
                    }
                    supabase.table("orders").insert(new_order).execute()
                    st.balloons()
                    st.success(f"Order placed for {prod['name']}! We'll contact you shortly.")
                    st.rerun()

# --- 2. PROTECTED STAFF LOGIN & PORTAL ---
elif portal_type == "🔐 Staff Login":
    
    if st.session_state["user"] is None:
        st.subheader("🔐 Staff Portal Authentication")
        
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            with st.form("login_form"):
                username_input = st.text_input("Username")
                password_input = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Sign In")
                
                if submit_button:
                    user_account = login_user(username_input.lower().strip(), password_input)
                    if user_account:
                        st.session_state["user"] = user_account
                        st.success(f"Welcome back, {user_account['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password.")

    else:
        current_user = st.session_state["user"]
        st.sidebar.markdown("---")
        st.sidebar.write(f"Logged in as: **{current_user['username']}**")
        st.sidebar.caption(f"Role: {current_user['role']}")
        
        if st.sidebar.button("🚪 Logout"):
            st.session_state["user"] = None
            st.rerun()

        # OWNER DASHBOARD
        if current_user["role"] == "Owner":
            st.markdown('<p class="main-header">📊 Owner Command Center</p>', unsafe_allow_html=True)
            st.markdown('<p class="sub-header">Manage shop revenue, live orders, and delivery driver assignments.</p>', unsafe_allow_html=True)
            
            # Key Performance Metrics
            m1, m2, m3 = st.columns(3)
            
            total_orders = len(df_orders) if not df_orders.empty else 0
            pending_orders = len(df_orders[df_orders["status"] != "Delivered"]) if not df_orders.empty else 0
            
            total_revenue = 0
            if not df_orders.empty and "price" in df_orders.columns:
                total_revenue = df_orders["price"].fillna(0).sum()
                
            m1.metric("Total Revenue", f"GH₵ {total_revenue:,.2f}")
            m2.metric("Total Orders", f"{total_orders}")
            m3.metric("Active Deliveries", f"{pending_orders}")
            
            st.markdown("---")

            with st.expander("➕ Register a New Driver Account"):
                with st.form("add_driver_form"):
                    new_driver_username = st.text_input("New Driver Username")
                    new_driver_password = st.text_input("New Driver Password", type="password")
                    add_driver_btn = st.form_submit_button("Create Driver Account")
                    
                    if add_driver_btn:
                        if new_driver_username and new_driver_password:
                            try:
                                supabase.table("users").insert({
                                    "username": new_driver_username.lower().strip(),
                                    "password": new_driver_password,
                                    "role": "Driver"
                                }).execute()
                                st.success(f"Driver '{new_driver_username}' created successfully!")
                                st.rerun()
                            except Exception:
                                st.error("Error creating driver. Username might already exist.")

            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📍 Live Delivery Map")
                if not df_orders.empty:
                    scatter_layer = pdk.Layer(
                        "ScatterplotLayer",
                        data=df_orders,
                        get_position=["lon", "lat"],
                        get_color="[46, 125, 50, 180]",
                        get_radius=120,
                        pickable=True
                    )
                    view_state = pdk.ViewState(latitude=df_orders["lat"].mean(), longitude=df_orders["lon"].mean(), zoom=12)
                    st.pydeck_chart(pdk.Deck(layers=[scatter_layer], initial_view_state=view_state, tooltip={"text": "Item: {item}\nStatus: {status}"}))
                else:
                    st.info("No active orders to display on map.")

            with col2:
                st.subheader("📦 Order Dispatch")
                if not df_orders.empty:
                    display_cols = ["id", "item", "customer", "status", "driver"]
                    st.dataframe(df_orders[display_cols], hide_index=True, use_container_width=True)
                    
                    driver_list = fetch_drivers()
                    selected_id = st.selectbox("Assign Driver to Order ID", df_orders["id"])
                    driver_name = st.selectbox("Select Driver", driver_list)
                    
                    if st.button("Assign Driver"):
                        supabase.table("orders").update({"driver": driver_name, "status": "Assigned"}).eq("id", selected_id).execute()
                        st.success(f"Order #{selected_id} assigned to {driver_name}")
                        st.rerun()
                else:
                    st.info("Waiting for incoming orders...")

        # DRIVER VIEW
        elif current_user["role"] == "Driver":
            st.markdown(f'<p class="main-header">🚚 Driver Portal: {current_user["username"].capitalize()}</p>', unsafe_allow_html=True)
            st.markdown('<p class="sub-header">View assigned orders and update delivery status on the go.</p>', unsafe_allow_html=True)
            
            if not df_orders.empty:
                my_orders = df_orders[df_orders["driver"] == current_user["username"]]
                
                if my_orders.empty:
                    st.info(f"No active deliveries assigned to {current_user['username']}.")
                else:
                    for idx, row in my_orders.iterrows():
                        with st.container():
                            st.subheader(f"Order #{row['id']} — {row['item']}")
                            st.write(f"👤 Customer: **{row['customer']}**")
                            st.write(f"📌 Current Status: **{row['status']}**")
                            
                            new_status = st.selectbox(
                                "Update Status", 
                                ["Assigned", "Out for Delivery", "Delivered"], 
                                index=["Assigned", "Out for Delivery", "Delivered"].index(row['status']) if row['status'] in ["Assigned", "Out for Delivery", "Delivered"] else 0,
                                key=f"status_{row['id']}"
                            )
                            if st.button(f"Update Order #{row['id']}", key=f"btn_{row['id']}"):
                                supabase.table("orders").update({"status": new_status}).eq("id", row["id"]).execute()
                                st.success("Status Updated!")
                                st.rerun()
                            st.markdown("---")
