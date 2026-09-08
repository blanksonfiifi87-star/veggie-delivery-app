import streamlit as st
import pandas as pd
import pydeck as pdk
import random
import os
from supabase import create_client

# Page Config
st.set_page_config(
    page_title="FreshVeggies Express",
    page_icon="🥦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN STYLING (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

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
    .section-banner {
        background-color: #f4fbf7;
        padding: 10px 18px;
        border-radius: 12px;
        border-left: 5px solid #2E7D32;
        font-size: 1.4rem;
        font-weight: 700;
        color: #2E7D32;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    .product-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
        margin-bottom: 15px;
    }
    .category-badge {
        background-color: #e8f5e9;
        color: #2e7d32;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        margin-bottom: 8px;
    }
    .product-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 4px;
    }
    .product-desc {
        font-size: 0.85rem;
        color: #666666;
        height: 38px;
        overflow: hidden;
        margin-bottom: 10px;
    }
    .price-text {
        font-size: 1.25rem;
        font-weight: 700;
        color: #2e7d32;
    }
</style>
""", unsafe_allow_html=True)

# --- SUPABASE INITIALIZATION ---
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

if "user" not in st.session_state:
    st.session_state["user"] = None

# Sidebar Branding
st.sidebar.title("🥦 FreshVeggies")
portal_type = st.sidebar.radio("Navigation", ["🛒 Customer Shop", "🔐 Staff Login"])

df_orders = fetch_orders()

# --- 10 PRODUCT CATALOG (ONLY GENERATED IMAGES) ---
catalog_sections = {
    "🥦 Fresh Vegetables": [
        {"name": "Local Tomatoes Basket", "price": 45, "img": "assets/tomatoes.jpg", "icon": "🍅", "desc": "Fresh Kumasi red tomatoes (5kg basket)"},
        {"name": "Fresh Onions Bag", "price": 50, "img": "assets/onions.jpg", "icon": "🧅", "desc": "Crisp red onions pack"},
        {"name": "Scotch Bonnet Peppers", "price": 25, "img": "assets/peppers.jpg", "icon": "🌶️", "desc": "Spicy Kpakpo shito & red peppers"},
        {"name": "Garden Eggs (Eggplant)", "price": 20, "img": "assets/garden_eggs.jpg", "icon": "🍆", "desc": "Local white garden eggs for stew"},
        {"name": "Fresh Okra Pack", "price": 15, "img": "assets/okra.jpg", "icon": "🫛", "desc": "Tender green okra pods"},
        {"name": "Carrot Bunch", "price": 18, "img": "assets/carrots.jpg", "icon": "🥕", "desc": "Sweet local organic carrots"},
        {"name": "Cabbage Head", "price": 20, "img": "assets/cabbage.jpg", "icon": "🥬", "desc": "Fresh crunchy cabbage"},
        {"name": "Cucumber Bunch", "price": 15, "img": "assets/cucumber.jpg", "icon": "🥒", "desc": "Cool crisp cucumbers"},
        {"name": "Green Bell Peppers", "price": 22, "img": "assets/green_peppers.jpg", "icon": "🫑", "desc": "Fresh green capsicum bell peppers"},
        {"name": "Red Bell Peppers", "price": 28, "img": "assets/red_peppers.jpg", "icon": "🫑", "desc": "Ripe sweet red bell peppers"}
    ]
}

# --- CUSTOMER SHOP ---
if portal_type == "🛒 Customer Shop":
    st.markdown('<p class="main-header">🥦 FreshVeggies Superstore</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Browse fresh market produce delivered directly across Kumasi.</p>', unsafe_allow_html=True)
    
    cust_name = st.text_input("Your Name / Phone Number (Required to place orders)", placeholder="e.g. Kwaku - 0244123456")
    search_query = st.text_input("🔍 Quick Search Catalog...", placeholder="e.g. Tomatoes, Pepper, Cabbage")

    st.markdown("---")

    for section_title, items in catalog_sections.items():
        display_items = items
        if search_query:
            display_items = [p for p in items if search_query.lower() in p["name"].lower() or search_query.lower() in p["desc"].lower()]
        
        if display_items:
            st.markdown(f'<div class="section-banner">{section_title}</div>', unsafe_allow_html=True)
            cols = st.columns(3)
            
            for idx, prod in enumerate(display_items):
                with cols[idx % 3]:
                    if os.path.exists(prod["img"]):
                        st.image(prod["img"], use_container_width=True)
                    else:
                        st.markdown(f"<h1 style='text-align: center; font-size: 4rem; margin: 10px 0;'>{prod['icon']}</h1>", unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="product-card">
                        <span class="category-badge">Fresh Produce</span>
                        <div class="product-title">{prod['name']}</div>
                        <div class="product-desc">{prod['desc']}</div>
                        <div class="price-text">GH₵ {prod['price']}.00</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🛒 Order {prod['name']}", key=f"btn_{section_title}_{idx}", use_container_width=True):
                        if not cust_name:
                            st.error("Please enter your name/phone number above first.")
                        else:
                            new_order = {
                                "item": str(prod["name"]),
                                "customer": str(cust_name),
                                "lat": round(6.688 + random.uniform(-0.015, 0.015), 6),
                                "lon": round(-1.624 + random.uniform(-0.015, 0.015), 6),
                                "status": "Pending",
                                "driver": "Unassigned",
                                "price": int(prod["price"])
                            }
                            supabase.table("orders").insert(new_order).execute()
                            st.balloons()
                            st.success(f"Order placed for {prod['name']}! We will reach out shortly.")
                            st.rerun()

# --- STAFF PORTAL ---
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

        if current_user["role"] == "Owner":
            st.markdown('<p class="main-header">📊 Owner Command Center</p>', unsafe_allow_html=True)
            st.markdown('<p class="sub-header">Manage shop revenue, live orders, and driver dispatch.</p>', unsafe_allow_html=True)
            
            m1, m2, m3 = st.columns(3)
            total_orders = len(df_orders) if not df_orders.empty else 0
            pending_orders = len(df_orders[df_orders["status"] != "Delivered"]) if not df_orders.empty else 0
            total_revenue = df_orders["price"].fillna(0).sum() if not df_orders.empty and "price" in df_orders.columns else 0
                
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
                                st.error("Error creating driver.")

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
                    st.dataframe(df_orders[["id", "item", "customer", "status", "driver"]], hide_index=True, use_container_width=True)
                    driver_list = fetch_drivers()
                    selected_id = st.selectbox("Assign Driver to Order ID", df_orders["id"])
                    driver_name = st.selectbox("Select Driver", driver_list)
                    
                    if st.button("Assign Driver"):
                        supabase.table("orders").update({"driver": driver_name, "status": "Assigned"}).eq("id", selected_id).execute()
                        st.success(f"Order #{selected_id} assigned to {driver_name}")
                        st.rerun()
                else:
                    st.info("Waiting for incoming orders...")

        elif current_user["role"] == "Driver":
            st.markdown(f'<p class="main-header">🚚 Driver Portal: {current_user["username"].capitalize()}</p>', unsafe_allow_html=True)
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
                            new_status = st.selectbox("Update Status", ["Assigned", "Out for Delivery", "Delivered"], key=f"status_{row['id']}")
                            if st.button(f"Update Order #{row['id']}", key=f"btn_{row['id']}"):
                                supabase.table("orders").update({"status": new_status}).eq("id", row["id"]).execute()
                                st.success("Status Updated!")
                                st.rerun()
                            st.markdown("---")
